const express = require('express');
const router = express.Router();
const upload = require('../middleware/upload');
const db = require('../utils/db');
const { v4: uuidv4 } = require('uuid');
const { runFullPipelineV2 } = require('../utils/pipeline_v2');

// Create new project
router.post('/', upload.array('roomPhoto', 10), async (req, res) => {
  try {
    const { email, name, tier, metadata } = req.body;
    const roomPhotos = req.files ? req.files.map(f => `/uploads/${f.filename}`) : [];
    const roomPhotoUrl = JSON.stringify(roomPhotos);

    if (!email || !tier) {
      return res.status(400).json({ error: 'Email and tier are required' });
    }

    // Check if client exists, otherwise create
    let clientResults = await db.query('SELECT id FROM clients WHERE email = ?', [email]);
    let clientId;

    if (clientResults.length === 0) {
      clientId = uuidv4();
      await db.query('INSERT INTO clients (id, email, name) VALUES (?, ?, ?)', [clientId, email, name || '']);
    } else {
      clientId = clientResults[0].id;
    }

    const projectId = uuidv4();
    const status = 'uploaded';
    
    await db.query('INSERT INTO projects (id, client_id, tier, status, room_photo_url, metadata) VALUES (?, ?, ?, ?, ?, ?)', 
                   [projectId, clientId, tier, status, roomPhotoUrl, JSON.stringify(metadata || {})]);

    // Trigger analysis in background
    if (roomPhotos.length > 0) {
      const fs = require('fs');
      const logFile = '/tmp/galerie-noire-backend.log';
      fs.appendFileSync(logFile, `Triggering pipeline v2 for ${projectId} with paths ${JSON.stringify(req.files.map(f => f.path))}\n`);
      runFullPipelineV2(projectId, req.files[0].path).then(() => {
        fs.appendFileSync(logFile, `Pipeline v2 finished for ${projectId}\n`);
      }).catch(err => {
        fs.appendFileSync(logFile, `Background pipeline v2 failed for ${projectId}: ${err.message}\n`);
        console.error('Background pipeline v2 failed:', err);
      });
    }

    res.status(201).json({
      id: projectId,
      clientId,
      status,
      roomPhotoUrls: roomPhotos
    });
  } catch (error) {
    console.error('Error creating project:', error);
    res.status(500).json({ error: 'Failed to create project' });
  }
});

// Get project status
router.get('/:id', async (req, res) => {
  try {
    const results = await db.query('SELECT * FROM projects WHERE id = ?', [req.params.id]);
    if (results.length === 0) {
      return res.status(404).json({ error: 'Project not found' });
    }
    
    const project = results[0];
    const deliverables = await db.query('SELECT * FROM deliverables WHERE project_id = ?', [req.params.id]);
    
    // Parse JSON content for all deliverables
    const parsedDeliverables = deliverables.map(d => {
      try {
        return { ...d, content: typeof d.content === 'string' ? JSON.parse(d.content) : d.content };
      } catch (e) {
        return d;
      }
    });

    // Helper to find specific deliverable types
    const findType = (type) => parsedDeliverables.find(d => d.type === type)?.content;

    res.json({
      ...project,
      metadata: typeof project.metadata === 'string' ? JSON.parse(project.metadata) : project.metadata,
      deliverables: parsedDeliverables,
      // Richer output mapping
      verified_profile: findType('verified_profile'),
      design_recommendations: findType('design_recommendations'),
      artwork_brief: findType('artwork_brief'),
      curated_deliverable: findType('curated_deliverable'),
      styling_guide: findType('styling_guide'),
      shopping_guide: findType('shopping_guide'),
      mockup: parsedDeliverables.find(d => d.type === 'room_mockup')
    });
  } catch (error) {
    console.error('Error fetching project:', error);
    res.status(500).json({ error: 'Failed to fetch project' });
  }
});

module.exports = router;
