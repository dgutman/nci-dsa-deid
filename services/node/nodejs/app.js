import express from 'express';

const app = express();
const PORT = 8080;

app.get('/', (req, res) => {
  res.send('<h1>HELLO WORLD</h1><p>Node.js service is running!</p>');
});

app.get('/api/*', (req, res) => {
  res.json({
    message: 'HELLO WORLD from API',
    path: req.path,
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server is running on http://0.0.0.0:${PORT}`);
});
