const express = require('express');
const router = express.Router();
const pool = require('../db/pool');
const { requireAuth, loadUser } = require('../middleware/auth');

router.get('/', requireAuth, loadUser, async (req, res) => {
  try {
    const { rows } = await pool.query('SELECT id, name, description FROM category ORDER BY name');
    res.json(rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  const { name, description } = req.body || {};
  if (!name || !name.trim()) return res.status(400).json({ error: 'Category name is required' });

  try {
    const existing = await pool.query('SELECT id FROM category WHERE name = $1', [name.trim()]);
    if (existing.rows.length) return res.status(409).json({ error: 'Category already exists' });

    const { rows } = await pool.query(
      'INSERT INTO category (name, description) VALUES ($1, $2) RETURNING id, name, description',
      [name.trim(), (description || '').trim()]
    );
    res.status(201).json(rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
