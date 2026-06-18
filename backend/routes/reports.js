const express = require('express');
const router = express.Router();
const pool = require('../db/pool');
const { requireAuth, loadUser } = require('../middleware/auth');

router.get('/stats', requireAuth, loadUser, async (req, res) => {
  if (!['admin', 'intern'].includes(req.user.role)) return res.status(403).json({ error: 'Access denied' });
  try {
    const { start, end } = req.query;
    let where = [];
    let params = [];
    let idx = 1;
    if (start) { where.push(`created_at >= $${idx++}`); params.push(new Date(start)); }
    if (end) { where.push(`created_at <= $${idx++}`); params.push(new Date(end)); }
    const whereClause = where.length ? 'WHERE ' + where.join(' AND ') : '';

    const countRes = await pool.query(`
      SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE status = 'open') AS open,
        COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress,
        COUNT(*) FILTER (WHERE status = 'resolved') AS resolved,
        COUNT(*) FILTER (WHERE status = 'closed') AS closed,
        COUNT(*) FILTER (WHERE status = 'escalated') AS escalated
      FROM ticket ${whereClause}
    `, params);
    const r = countRes.rows[0];

    const { rows: cats } = await pool.query(`SELECT id, name FROM category`);
    const byCategory = [];
    for (const c of cats) {
      const cRes = await pool.query(
        `SELECT COUNT(*) FROM ticket ${whereClause ? whereClause + ' AND' : 'WHERE'} category_id = $${idx}`,
        [...params, c.id]
      );
      const cnt = parseInt(cRes.rows[0].count);
      if (cnt > 0) byCategory.push({ category: c.name, count: cnt });
    }

    const byPriority = [];
    for (const p of ['low', 'medium', 'high', 'urgent']) {
      const pRes = await pool.query(
        `SELECT COUNT(*) FROM ticket ${whereClause ? whereClause + ' AND' : 'WHERE'} priority = $${idx}`,
        [...params, p]
      );
      byPriority.push({ priority: p, count: parseInt(pRes.rows[0].count) });
    }

    const daily = [];
    for (let i = 29; i >= 0; i--) {
      const day = new Date();
      day.setUTCDate(day.getUTCDate() - i);
      const dayStr = day.toISOString().split('T')[0];
      const { rows } = await pool.query(
        `SELECT COUNT(*) FROM ticket WHERE created_at::date = $1::date`,
        [dayStr]
      );
      daily.push({ date: dayStr, count: parseInt(rows[0].count) });
    }

    res.json({
      total: parseInt(r.total),
      open: parseInt(r.open),
      in_progress: parseInt(r.in_progress),
      resolved: parseInt(r.resolved),
      closed: parseInt(r.closed),
      escalated: parseInt(r.escalated),
      by_category: byCategory,
      by_priority: byPriority,
      daily_volume: daily,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
