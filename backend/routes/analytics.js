const express = require('express');
const router = express.Router();
const pool = require('../db/pool');
const { requireAuth, loadUser } = require('../middleware/auth');

router.get('/stats', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  try {
    const { rows: totals } = await pool.query(`
      SELECT COUNT(*) AS total,
             COUNT(*) FILTER (WHERE status IN ('resolved', 'closed')) AS resolved
      FROM ticket
    `);
    const total = parseInt(totals[0].total);
    const resolved = parseInt(totals[0].resolved);
    const slaCompliance = total > 0 ? Math.round((resolved / total) * 1000) / 10 : 0;

    const { rows: staff } = await pool.query(
      `SELECT u.id, u.full_name, COUNT(ta.ticket_id) AS cnt
       FROM "user" u
       LEFT JOIN ticket_assignees ta ON ta.user_id = u.id
       WHERE u.role IN ('admin', 'intern')
       GROUP BY u.id, u.full_name
       HAVING COUNT(ta.ticket_id) > 0
       ORDER BY cnt DESC LIMIT 10`
    );

    res.json({
      total_tickets: total,
      resolved_tickets: resolved,
      sla_compliance: slaCompliance,
      assignee_workload: staff.map(s => ({ name: s.full_name, count: parseInt(s.cnt) })),
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
