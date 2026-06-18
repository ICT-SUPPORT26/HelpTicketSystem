const express = require('express');
const router = express.Router();
const pool = require('../db/pool');
const { requireAuth, loadUser } = require('../middleware/auth');
const { ticketToDict } = require('../utils/serializers');
const { buildTicketFull } = require('./tickets');

router.get('/stats', requireAuth, loadUser, async (req, res) => {
  try {
    const user = req.user;
    let total, open, inProgress, resolved, closed, escalated, pendingUsers = 0;
    let recentRows;

    if (user.role === 'admin') {
      const counts = await pool.query(`
        SELECT
          COUNT(*) AS total,
          COUNT(*) FILTER (WHERE status = 'open') AS open,
          COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress,
          COUNT(*) FILTER (WHERE status = 'resolved') AS resolved,
          COUNT(*) FILTER (WHERE status = 'closed') AS closed,
          COUNT(*) FILTER (WHERE status = 'escalated') AS escalated
        FROM ticket
      `);
      const r = counts.rows[0];
      total = parseInt(r.total);
      open = parseInt(r.open);
      inProgress = parseInt(r.in_progress);
      resolved = parseInt(r.resolved);
      closed = parseInt(r.closed);
      escalated = parseInt(r.escalated);

      const pendRes = await pool.query(
        `SELECT COUNT(*) FROM "user" WHERE role = 'intern' AND is_approved = FALSE`
      );
      pendingUsers = parseInt(pendRes.rows[0].count);

      const { rows } = await pool.query(
        `SELECT id FROM ticket ORDER BY created_at DESC LIMIT 5`
      );
      recentRows = rows;

    } else if (user.role === 'intern') {
      const { rows: assigned } = await pool.query(
        `SELECT t.id, t.status FROM ticket t JOIN ticket_assignees ta ON ta.ticket_id = t.id WHERE ta.user_id = $1`,
        [user.id]
      );
      const assignedIds = assigned.map(r => r.id);
      total = assignedIds.length;
      open = assigned.filter(r => r.status === 'open').length;
      inProgress = assigned.filter(r => r.status === 'in_progress').length;
      resolved = assigned.filter(r => r.status === 'resolved').length;
      closed = assigned.filter(r => r.status === 'closed').length;
      escalated = assigned.filter(r => r.status === 'escalated').length;

      if (assignedIds.length) {
        const { rows } = await pool.query(
          `SELECT id FROM ticket WHERE id = ANY($1::int[]) ORDER BY created_at DESC LIMIT 5`,
          [assignedIds]
        );
        recentRows = rows;
      } else {
        recentRows = [];
      }
    } else {
      const counts = await pool.query(`
        SELECT
          COUNT(*) AS total,
          COUNT(*) FILTER (WHERE status = 'open') AS open,
          COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress,
          COUNT(*) FILTER (WHERE status = 'resolved') AS resolved,
          COUNT(*) FILTER (WHERE status = 'closed') AS closed,
          COUNT(*) FILTER (WHERE status = 'escalated') AS escalated
        FROM ticket WHERE created_by_id = $1
      `, [user.id]);
      const r = counts.rows[0];
      total = parseInt(r.total);
      open = parseInt(r.open);
      inProgress = parseInt(r.in_progress);
      resolved = parseInt(r.resolved);
      closed = parseInt(r.closed);
      escalated = parseInt(r.escalated);

      const { rows } = await pool.query(
        `SELECT id FROM ticket WHERE created_by_id = $1 ORDER BY created_at DESC LIMIT 5`,
        [user.id]
      );
      recentRows = rows;
    }

    const recentTickets = [];
    for (const row of recentRows) {
      const t = await buildTicketFull(row.id);
      if (t) recentTickets.push(ticketToDict(t));
    }

    res.json({ total, open, in_progress: inProgress, resolved, closed, escalated, pending_users: pendingUsers, recent_tickets: recentTickets });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
