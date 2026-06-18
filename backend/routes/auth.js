const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const pool = require('../db/pool');
const { requireAuth, loadUser, JWT_SECRET } = require('../middleware/auth');
const { userToDict } = require('../utils/serializers');

const ACCESS_EXPIRES = '30m';
const REFRESH_EXPIRES = '7d';

function signAccess(userId) {
  return jwt.sign({ sub: String(userId) }, JWT_SECRET, { expiresIn: ACCESS_EXPIRES });
}
function signRefresh(userId) {
  return jwt.sign({ sub: String(userId), refresh: true }, JWT_SECRET, { expiresIn: REFRESH_EXPIRES });
}

router.post('/login', async (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password are required' });
  }
  try {
    const { rows } = await pool.query('SELECT * FROM "user" WHERE username = $1', [username.trim()]);
    const user = rows[0];
    if (!user) return res.status(401).json({ error: 'Invalid username or password' });

    const match = await bcrypt.compare(password, user.password_hash);
    if (!match) return res.status(401).json({ error: 'Invalid username or password' });

    if (!user.is_active) return res.status(403).json({ error: 'Account is deactivated. Contact administrator.' });
    if (!user.is_verified) return res.status(403).json({ error: 'Email not verified. Please verify your email.' });
    if (user.role === 'intern' && !user.is_approved) return res.status(403).json({ error: 'Intern account pending admin approval.' });

    res.json({
      access_token: signAccess(user.id),
      refresh_token: signRefresh(user.id),
      user: userToDict(user),
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/refresh', async (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Refresh token required' });
  }
  const token = authHeader.slice(7);
  try {
    const payload = jwt.verify(token, JWT_SECRET);
    if (!payload.refresh) return res.status(401).json({ error: 'Not a refresh token' });
    res.json({ access_token: signAccess(payload.sub) });
  } catch (err) {
    res.status(401).json({ error: 'Invalid or expired refresh token' });
  }
});

router.get('/me', requireAuth, loadUser, (req, res) => {
  res.json(userToDict(req.user));
});

router.post('/logout', requireAuth, (req, res) => {
  res.json({ message: 'Logged out successfully' });
});

router.put('/change-password', requireAuth, loadUser, async (req, res) => {
  const { current_password, new_password } = req.body || {};
  if (!current_password || !new_password) {
    return res.status(400).json({ error: 'current_password and new_password are required' });
  }
  const match = await bcrypt.compare(current_password, req.user.password_hash);
  if (!match) return res.status(400).json({ error: 'Current password is incorrect' });
  if (new_password.length < 6) return res.status(400).json({ error: 'New password must be at least 6 characters' });

  const hash = await bcrypt.hash(new_password, 10);
  await pool.query('UPDATE "user" SET password_hash = $1 WHERE id = $2', [hash, req.user.id]);
  res.json({ message: 'Password changed successfully' });
});

module.exports = router;
