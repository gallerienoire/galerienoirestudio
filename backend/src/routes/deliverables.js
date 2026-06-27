const express = require('express');
const router = express.Router();
const db = require('../utils/db');
const { v4: uuidv4 } = require('uuid');

// Add deliverable to project
router.post('/:projectId/deliverables', async (req, res) => {
  try {
    const { type, fileUrl, content } = req.body;
    const { projectId } = req.params;

    if (!type) {
      return res.status(400).json({ error: 'Type is required' });
    }

    // Verify project exists
    const projectResults = await db.query('SELECT id FROM projects WHERE id = ?', [projectId]);
    if (projectResults.length === 0) {
      return res.status(404).json({ error: 'Project not found' });
    }

    const deliverableId = uuidv4();
    await db.query('INSERT INTO deliverables (id, project_id, type, file_url, content) VALUES (?, ?, ?, ?, ?)', 
                    [deliverableId, projectId, type, fileUrl || '', JSON.stringify(content || {})]);

    res.status(201).json({
      id: deliverableId,
      projectId,
      type
    });
  } catch (error) {
    console.error('Error adding deliverable:', error);
    res.status(500).json({ error: 'Failed to add deliverable' });
  }
});

// Get deliverables for a project
router.get('/:projectId/deliverables', async (req, res) => {
  try {
    const results = await db.query('SELECT * FROM deliverables WHERE project_id = ?', [req.params.projectId]);
    res.json(results);
  } catch (error) {
    console.error('Error fetching deliverables:', error);
    res.status(500).json({ error: 'Failed to fetch deliverables' });
  }
});

module.exports = router;
