const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());

// Log requests
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Payments route first because it handles its own parsing for webhook
app.use('/api', require('./routes/payments'));

app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// Serve brand design assets
app.use('/design', express.static('/home/team/shared/design'));

// Serve AI pipeline generated artwork
app.use('/artwork', express.static('/home/team/shared/ai-pipeline/generated-artwork'));

// API Routes
app.use('/api/projects', require('./routes/projects'));
app.use('/api/projects', require('./routes/deliverables'));
app.use('/api/clients', require('./routes/clients'));

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Serve website pages (static HTML)
const websitePath = '/home/team/shared/website';
app.use(express.static(websitePath));

// Fallback to index.html for unknown routes
app.use((req, res) => {
  // If it's an API route that wasn't matched, return 404
  if (req.url.startsWith('/api')) {
    return res.status(404).json({ error: 'API route not found' });
  }
  res.sendFile(path.join(websitePath, 'index.html'), (err) => {
    if (err) {
      if (!res.headersSent) {
        res.status(404).send('Page not found');
      }
    }
  });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Galerie Noire API listening at http://0.0.0.0:${port}`);
});
