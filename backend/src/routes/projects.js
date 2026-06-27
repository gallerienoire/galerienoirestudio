const express = require('express');
const router = express.Router();
const upload = require('../middleware/upload');
const db = require('../utils/db');
const { v4: uuidv4 } = require('uuid');
const { runRoomAnalysis } = require('../utils/pipeline');

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
      fs.appendFileSync(logFile, `Triggering analysis for ${projectId} with paths ${JSON.stringify(req.files.map(f => f.path))}\n`);
      runRoomAnalysis(projectId, req.files.map(f => f.path)).then(() => {
        fs.appendFileSync(logFile, `Analysis finished for ${projectId}\n`);
      }).catch(err => {
        fs.appendFileSync(logFile, `Background analysis failed for ${projectId}: ${err.message}\n`);
        console.error('Background analysis failed:', err);
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
    
    res.json({
      ...project,
      deliverables
    });
  } catch (error) {
    console.error('Error fetching project:', error);
    res.status(500).json({ error: 'Failed to fetch project' });
  }
});

module.exports = router;
