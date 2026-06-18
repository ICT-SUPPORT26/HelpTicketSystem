const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const pool = require('../db/pool');
const { requireAuth, loadUser } = require('../middleware/auth');
const { userToDict } = require('../utils/serializers');

router.get('/staff', requireAuth, loadUser, async (req, res) => {
  if (!['admin', 'intern'].includes(req.user.role)) return res.status(403).json({ error: 'Access denied' });
  try {
    const { rows } = await pool.query(
      `SELECT * FROM "user" WHERE role IN ('admin', 'intern') ORDER BY full_name`
    );
    res.json(rows.map(userToDict));
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/interns/pending', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  try {
    const { rows } = await pool.query(`SELECT * FROM "user" WHERE role = 'intern' AND is_approved = FALSE`);
    res.json(rows.map(userToDict));
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/interns/stats', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  try {
    const { rows: interns } = await pool.query(`SELECT * FROM "user" WHERE role = 'intern' ORDER BY full_name`);
    const result = [];
    for (const intern of interns) {
      const { rows: assigned } = await pool.query(
        `SELECT t.id, t.status FROM ticket t
         JOIN ticket_assignees ta ON ta.ticket_id = t.id
         WHERE ta.user_id = $1`, [intern.id]
      );
      const assignedIds = assigned.map(r => r.id);
      const open = assigned.filter(r => r.status === 'open').length;
      const inProgress = assigned.filter(r => r.status === 'in_progress').length;
      const resolved = assigned.filter(r => ['resolved', 'closed'].includes(r.status)).length;
      const escalated = assigned.filter(r => r.status === 'escalated').length;
      result.push({
        ...userToDict(intern),
        total_assigned: assignedIds.length,
        open, in_progress: inProgress, resolved, escalated,
      });
    }
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  const page = parseInt(req.query.page) || 1;
  const perPage = parseInt(req.query.per_page) || 20;
  const roleFilter = req.query.role || '';
  const search = req.query.search || '';
  const offset = (page - 1) * perPage;

  let where = [];
  let params = [];
  let idx = 1;
  if (roleFilter) { where.push(`role = $${idx++}`); params.push(roleFilter); }
  if (search) {
    where.push(`(username ILIKE $${idx} OR full_name ILIKE $${idx} OR email ILIKE $${idx})`);
    params.push(`%${search}%`); idx++;
  }
  const whereClause = where.length ? 'WHERE ' + where.join(' AND ') : '';

  try {
    const countRes = await pool.query(`SELECT COUNT(*) FROM "user" ${whereClause}`, params);
    const total = parseInt(countRes.rows[0].count);
    const { rows } = await pool.query(
      `SELECT * FROM "user" ${whereClause} ORDER BY created_at DESC LIMIT $${idx} OFFSET $${idx + 1}`,
      [...params, perPage, offset]
    );
    res.json({
      users: rows.map(userToDict),
      total,
      pages: Math.ceil(total / perPage),
      current_page: page,
    });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  const { username, email, full_name, password, role } = req.body || {};
  if (!username || !email || !full_name || !password) {
    return res.status(400).json({ error: 'username, email, full_name, password are required' });
  }
  try {
    const dupUsername = await pool.query(`SELECT id FROM "user" WHERE username = $1`, [username]);
    if (dupUsername.rows.length) return res.status(409).json({ error: 'Username already exists' });
    const dupEmail = await pool.query(`SELECT id FROM "user" WHERE email = $1`, [email]);
    if (dupEmail.rows.length) return res.status(409).json({ error: 'Email already exists' });
    const hash = await bcrypt.hash(password, 10);
    const { rows } = await pool.query(
      `INSERT INTO "user" (username, email, full_name, password_hash, role, is_active, is_verified, is_approved)
       VALUES ($1, $2, $3, $4, $5, TRUE, TRUE, TRUE) RETURNING *`,
      [username, email, full_name, hash, role || 'user']
    );
    res.status(201).json(userToDict(rows[0]));
  } catch (err) {
    if (err.code === '23505') return res.status(409).json({ error: 'Username or email already exists' });
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/:id', requireAuth, loadUser, async (req, res) => {
  const userId = parseInt(req.params.id);
  if (req.user.role !== 'admin' && req.user.id !== userId) return res.status(403).json({ error: 'Access denied' });
  try {
    const { rows } = await pool.query(`SELECT * FROM "user" WHERE id = $1`, [userId]);
    if (!rows.length) return res.status(404).json({ error: 'User not found' });
    res.json(userToDict(rows[0]));
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.delete('/:id', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  const userId = parseInt(req.params.id);
  if (req.user.id === userId) return res.status(400).json({ error: 'Cannot delete yourself' });
  try {
    const result = await pool.query(`DELETE FROM "user" WHERE id = $1`, [userId]);
    if (result.rowCount === 0) return res.status(404).json({ error: 'User not found' });
    res.json({ message: 'User deleted' });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/:id/toggle-status', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  const userId = parseInt(req.params.id);
  try {
    const { rows } = await pool.query(
      `UPDATE "user" SET is_active = NOT is_active WHERE id = $1 RETURNING id, is_active`,
      [userId]
    );
    if (!rows.length) return res.status(404).json({ error: 'User not found' });
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/:id/approve', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  const userId = parseInt(req.params.id);
  try {
    const { rows } = await pool.query(
      `UPDATE "user" SET is_approved = TRUE, is_active = TRUE, approved_by_id = $1, approved_at = NOW()
       WHERE id = $2 RETURNING *`,
      [req.user.id, userId]
    );
    if (!rows.length) return res.status(404).json({ error: 'User not found' });
    res.json(userToDict(rows[0]));
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/:id/reset-password', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  const { new_password } = req.body || {};
  if (!new_password || new_password.length < 6) {
    return res.status(400).json({ error: 'Password must be at least 6 characters' });
  }
  const hash = await bcrypt.hash(new_password, 10);
  const { rowCount } = await pool.query(
    `UPDATE "user" SET password_hash = $1 WHERE id = $2`,
    [hash, parseInt(req.params.id)]
  );
  if (!rowCount) return res.status(404).json({ error: 'User not found' });
  res.json({ message: 'Password reset successfully' });
});

module.exports = router;
