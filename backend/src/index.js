const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
// Payments route first because it handles its own parsing for webhook
app.use('/api', require('./routes/payments'));
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// Serve brand design assets
app.use('/design', express.static('/home/team/shared/design'));

// Serve website pages (static HTML)
app.use(express.static('/home/team/shared/website'));

// Serve AI pipeline generated artwork
app.use('/artwork', express.static('/home/team/shared/ai-pipeline/generated-artwork'));

// Routes
app.use('/api/projects', require('./routes/projects'));
app.use('/api/projects', require('./routes/deliverables'));
app.use('/api/clients', require('./routes/clients'));

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Galerie Noire API listening at http://0.0.0.0:${port}`);
});
