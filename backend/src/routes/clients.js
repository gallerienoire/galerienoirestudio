const express = require('express');
const router = express.Router();
const db = require('../utils/db');

// Get all clients
router.get('/', async (req, res) => {
  try {
    const results = await db.query('SELECT * FROM clients');
    res.json(results);
  } catch (error) {
    console.error('Error fetching clients:', error);
    res.status(500).json({ error: 'Failed to fetch clients' });
  }
});

// Get projects for a client
router.get('/:id/projects', async (req, res) => {
  try {
    const results = await db.query('SELECT * FROM projects WHERE client_id = ?', [req.params.id]);
    res.json(results);
  } catch (error) {
    console.error('Error fetching client projects:', error);
    res.status(500).json({ error: 'Failed to fetch client projects' });
  }
});

module.exports = router;
