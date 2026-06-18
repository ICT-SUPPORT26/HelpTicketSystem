const express = require('express');
const router = express.Router();
const pool = require('../db/pool');
const { requireAuth, loadUser } = require('../middleware/auth');
const { notificationToDict } = require('../utils/serializers');

router.get('/unread-count', requireAuth, loadUser, async (req, res) => {
  try {
    const { rows } = await pool.query(
      `SELECT COUNT(*) FROM notification WHERE user_id = $1 AND is_read = FALSE`,
      [req.user.id]
    );
    res.json({ count: parseInt(rows[0].count) });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/recent', requireAuth, loadUser, async (req, res) => {
  try {
    const since = req.query.since;
    let query = `SELECT * FROM notification WHERE user_id = $1`;
    const params = [req.user.id];
    if (since) {
      const sinceDate = new Date(since);
      if (!isNaN(sinceDate.getTime())) {
        query += ` AND created_at > $2`;
        params.push(sinceDate);
      }
    }
    query += ` ORDER BY created_at DESC LIMIT 10`;
    const { rows } = await pool.query(query, params);
    const { rows: unreadRows } = await pool.query(
      `SELECT COUNT(*) FROM notification WHERE user_id = $1 AND is_read = FALSE`,
      [req.user.id]
    );
    res.json({
      notifications: rows.map(notificationToDict),
      unread_count: parseInt(unreadRows[0].count),
    });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/settings', requireAuth, loadUser, async (req, res) => {
  try {
    const { rows } = await pool.query(
      `SELECT * FROM notification_settings WHERE user_id = $1`,
      [req.user.id]
    );
    if (!rows.length) {
      return res.json({
        new_ticket_email: true, new_ticket_app: true,
        ticket_updated_email: true, ticket_updated_app: true,
        new_comment_email: true, new_comment_app: true,
        ticket_closed_email: true, ticket_closed_app: true,
        ticket_overdue_email: true, ticket_overdue_app: true,
        do_not_disturb: false, dnd_start_time: null, dnd_end_time: null,
      });
    }
    const s = rows[0];
    res.json({
      new_ticket_email: s.new_ticket_email,
      new_ticket_app: s.new_ticket_app,
      ticket_updated_email: s.ticket_updated_email,
      ticket_updated_app: s.ticket_updated_app,
      new_comment_email: s.new_comment_email,
      new_comment_app: s.new_comment_app,
      ticket_closed_email: s.ticket_closed_email,
      ticket_closed_app: s.ticket_closed_app,
      ticket_overdue_email: s.ticket_overdue_email,
      ticket_overdue_app: s.ticket_overdue_app,
      do_not_disturb: s.do_not_disturb,
      dnd_start_time: s.dnd_start_time || null,
      dnd_end_time: s.dnd_end_time || null,
    });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.put('/settings', requireAuth, loadUser, async (req, res) => {
  const data = req.body || {};
  const boolFields = [
    'new_ticket_email', 'new_ticket_app',
    'ticket_updated_email', 'ticket_updated_app',
    'new_comment_email', 'new_comment_app',
    'ticket_closed_email', 'ticket_closed_app',
    'ticket_overdue_email', 'ticket_overdue_app',
    'do_not_disturb',
  ];
  try {
    const { rows } = await pool.query(
      `SELECT id FROM notification_settings WHERE user_id = $1`,
      [req.user.id]
    );
    if (!rows.length) {
      await pool.query(`INSERT INTO notification_settings (user_id) VALUES ($1)`, [req.user.id]);
    }
    const sets = [];
    const vals = [];
    let idx = 1;
    for (const f of boolFields) {
      if (f in data) { sets.push(`${f} = $${idx++}`); vals.push(!!data[f]); }
    }
    for (const tf of ['dnd_start_time', 'dnd_end_time']) {
      if (data[tf]) { sets.push(`${tf} = $${idx++}`); vals.push(data[tf]); }
    }
    if (sets.length) {
      vals.push(req.user.id);
      await pool.query(
        `UPDATE notification_settings SET ${sets.join(', ')} WHERE user_id = $${idx}`,
        vals
      );
    }
    res.json({ message: 'Settings saved' });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/mark-all-read', requireAuth, loadUser, async (req, res) => {
  try {
    await pool.query(
      `UPDATE notification SET is_read = TRUE, read_at = NOW() WHERE user_id = $1 AND is_read = FALSE`,
      [req.user.id]
    );
    res.json({ message: 'All notifications marked as read' });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/clear-all', requireAuth, loadUser, async (req, res) => {
  try {
    await pool.query(`DELETE FROM notification WHERE user_id = $1`, [req.user.id]);
    res.json({ message: 'All notifications cleared' });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/', requireAuth, loadUser, async (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const perPage = parseInt(req.query.per_page) || 20;
  const offset = (page - 1) * perPage;
  try {
    const countRes = await pool.query(
      `SELECT COUNT(*) FROM notification WHERE user_id = $1`, [req.user.id]
    );
    const total = parseInt(countRes.rows[0].count);
    const { rows } = await pool.query(
      `SELECT * FROM notification WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3`,
      [req.user.id, perPage, offset]
    );
    const unreadRes = await pool.query(
      `SELECT COUNT(*) FROM notification WHERE user_id = $1 AND is_read = FALSE`,
      [req.user.id]
    );
    res.json({
      notifications: rows.map(notificationToDict),
      total,
      unread: parseInt(unreadRes.rows[0].count),
    });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/:id/mark-read', requireAuth, loadUser, async (req, res) => {
  try {
    const { rows } = await pool.query(
      `UPDATE notification SET is_read = TRUE, read_at = NOW()
       WHERE id = $1 AND user_id = $2 RETURNING id, is_read`,
      [parseInt(req.params.id), req.user.id]
    );
    if (!rows.length) return res.status(404).json({ error: 'Notification not found' });
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
