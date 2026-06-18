require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const fs = require('fs');
const { requireAuth, loadUser } = require('./middleware/auth');
const { initSchema } = require('./db/schema');
const pool = require('./db/pool');

const app = express();
const PORT = parseInt(process.env.BACKEND_PORT || process.env.PORT || '8000', 10);

app.set('trust proxy', 1);

app.use(helmet({ crossOriginResourcePolicy: { policy: 'cross-origin' } }));
app.use(cors({
  origin: true,
  credentials: true,
}));
app.use(express.json({ limit: '16mb' }));
app.use(express.urlencoded({ extended: true, limit: '16mb' }));

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 500,
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/', limiter);

const UPLOAD_DIR = path.join(__dirname, '../uploads');
if (!fs.existsSync(UPLOAD_DIR)) fs.mkdirSync(UPLOAD_DIR, { recursive: true });

const authRoutes = require('./routes/auth');
const ticketRoutes = require('./routes/tickets');
const categoryRoutes = require('./routes/categories');
const userRoutes = require('./routes/users');
const notificationRoutes = require('./routes/notifications');
const dashboardRoutes = require('./routes/dashboard');
const reportRoutes = require('./routes/reports');
const analyticsRoutes = require('./routes/analytics');

app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/tickets', ticketRoutes);
app.use('/api/v1/categories', categoryRoutes);
app.use('/api/v1/users', userRoutes);
app.use('/api/v1/notifications', notificationRoutes);
app.use('/api/v1/dashboard', dashboardRoutes);
app.use('/api/v1/reports', reportRoutes);
app.use('/api/v1/analytics', analyticsRoutes);

app.get('/api/v1/attachments/:filename', requireAuth, loadUser, async (req, res) => {
  const { filename } = req.params;
  const user = req.user;
  try {
    const { rows } = await pool.query(
      `SELECT a.*, t.created_by_id AS ticket_created_by_id, t.id AS ticket_id_ref
       FROM attachment a JOIN ticket t ON t.id = a.ticket_id WHERE a.filename = $1`,
      [filename]
    );
    if (!rows.length) return res.status(404).json({ error: 'File not found' });
    const att = rows[0];

    if (user.role === 'user' && att.ticket_created_by_id !== user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    if (user.role === 'intern') {
      const { rows: assigned } = await pool.query(
        `SELECT 1 FROM ticket_assignees WHERE ticket_id = $1 AND user_id = $2`,
        [att.ticket_id_ref, user.id]
      );
      if (!assigned.length && att.ticket_created_by_id !== user.id) {
        return res.status(403).json({ error: 'Access denied' });
      }
    }

    res.sendFile(path.join(UPLOAD_DIR, filename));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

const REACT_DIST = path.join(__dirname, '../frontend/dist');
if (fs.existsSync(REACT_DIST)) {
  app.use(express.static(REACT_DIST));
  app.get('*', (req, res) => {
    if (!req.path.startsWith('/api/') && !req.path.startsWith('/uploads/')) {
      res.sendFile(path.join(REACT_DIST, 'index.html'));
    }
  });
}

app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

async function start() {
  try {
    await initSchema();
    app.listen(PORT, '0.0.0.0', () => {
      console.log(`Express backend running on http://0.0.0.0:${PORT}`);
    });
  } catch (err) {
    console.error('Failed to start server:', err);
    process.exit(1);
  }
}

start();
