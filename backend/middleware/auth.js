const jwt = require('jsonwebtoken');
const pool = require('../db/pool');

const JWT_SECRET = process.env.SESSION_SECRET || 'dev-jwt-helpdesk-secret-CHANGE-BEFORE-DEPLOY';

function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid Authorization header' });
  }
  const token = authHeader.slice(7);
  try {
    const payload = jwt.verify(token, JWT_SECRET);
    if (payload.refresh === true) {
      return res.status(401).json({ error: 'Refresh tokens cannot be used for API access' });
    }
    req.userId = parseInt(payload.sub || payload.identity || payload.id, 10);
    req.tokenPayload = payload;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Token expired or invalid' });
  }
}

async function loadUser(req, res, next) {
  try {
    const { rows } = await pool.query('SELECT * FROM "user" WHERE id = $1', [req.userId]);
    if (!rows.length) return res.status(401).json({ error: 'User not found' });
    req.user = rows[0];
    next();
  } catch (err) {
    next(err);
  }
}

module.exports = { requireAuth, loadUser, JWT_SECRET };
