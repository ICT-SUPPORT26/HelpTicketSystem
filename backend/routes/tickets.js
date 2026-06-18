const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');
const pool = require('../db/pool');
const { requireAuth, loadUser } = require('../middleware/auth');
const { ticketToDict, commentToDict, historyToDict, attachmentToDict } = require('../utils/serializers');
const { notifyNewTicket, notifyTicketUpdated, notifyNewComment, notifyTicketClosed } = require('../services/notifications');

const UPLOAD_DIR = path.join(__dirname, '../../uploads');
const ALLOWED_EXTENSIONS = new Set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx']);

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOAD_DIR),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    cb(null, `${uuidv4()}${ext}`);
  },
});
const upload = multer({
  storage,
  limits: { fileSize: 16 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).slice(1).toLowerCase();
    cb(null, ALLOWED_EXTENSIONS.has(ext));
  },
});

async function getAssignedIds(userId) {
  const { rows } = await pool.query(
    `SELECT ticket_id FROM ticket_assignees WHERE user_id = $1`,
    [userId]
  );
  return rows.map(r => r.ticket_id);
}

async function buildTicketFull(ticketId) {
  const { rows } = await pool.query(`
    SELECT t.*,
      c.name AS category_name,
      u.full_name AS creator_full_name, u.username AS creator_username,
      cb.full_name AS closed_by_full_name,
      eb.full_name AS escalated_by_full_name
    FROM ticket t
    LEFT JOIN category c ON c.id = t.category_id
    LEFT JOIN "user" u ON u.id = t.created_by_id
    LEFT JOIN "user" cb ON cb.id = t.closed_by_id
    LEFT JOIN "user" eb ON eb.id = t.escalated_by_id
    WHERE t.id = $1
  `, [ticketId]);
  if (!rows.length) return null;
  const t = rows[0];

  const { rows: assigneeRows } = await pool.query(`
    SELECT u.id, u.full_name, u.username FROM "user" u
    JOIN ticket_assignees ta ON ta.user_id = u.id
    WHERE ta.ticket_id = $1
  `, [ticketId]);
  t.assignees = assigneeRows;

  const { rows: attachRows } = await pool.query(
    `SELECT * FROM attachment WHERE ticket_id = $1 ORDER BY created_at`, [ticketId]
  );
  t.attachments = attachRows.map(attachmentToDict);

  const { rows: commentRows } = await pool.query(`
    SELECT cm.*, u.full_name AS author_full_name, u.role AS author_role
    FROM comment cm
    LEFT JOIN "user" u ON u.id = cm.author_id
    WHERE cm.ticket_id = $1 ORDER BY cm.created_at
  `, [ticketId]);
  t.comments = commentRows.map(commentToDict);

  const { rows: histRows } = await pool.query(`
    SELECT h.*, u.full_name AS user_full_name FROM ticket_history h
    LEFT JOIN "user" u ON u.id = h.user_id
    WHERE h.ticket_id = $1 ORDER BY h.timestamp
  `, [ticketId]);
  t.history = histRows.map(historyToDict);

  const { rows: countRow } = await pool.query(
    `SELECT COUNT(*) FROM comment WHERE ticket_id = $1`, [ticketId]
  );
  t.comment_count = parseInt(countRow[0].count);

  return t;
}

async function recordHistory(client, ticketId, userId, action, field = null, oldVal = null, newVal = null) {
  await client.query(
    `INSERT INTO ticket_history (ticket_id, user_id, action, field_changed, old_value, new_value)
     VALUES ($1, $2, $3, $4, $5, $6)`,
    [ticketId, userId, action, field, oldVal != null ? String(oldVal) : null, newVal != null ? String(newVal) : null]
  );
}

router.get('/', requireAuth, loadUser, async (req, res) => {
  const user = req.user;
  const page = parseInt(req.query.page) || 1;
  const perPage = Math.min(parseInt(req.query.per_page) || 20, 100);
  const status = req.query.status || '';
  const priority = req.query.priority || '';
  const categoryId = req.query.category_id ? parseInt(req.query.category_id) : null;
  const search = req.query.search || '';
  const offset = (page - 1) * perPage;

  try {
    let conditions = [];
    let params = [];
    let idx = 1;

    if (user.role === 'intern') {
      const assignedIds = await getAssignedIds(user.id);
      if (!assignedIds.length) {
        return res.json({ tickets: [], total: 0, pages: 0, current_page: page, per_page: perPage });
      }
      conditions.push(`t.id = ANY($${idx++}::int[])`);
      params.push(assignedIds);
    } else if (user.role === 'user') {
      conditions.push(`t.created_by_id = $${idx++}`);
      params.push(user.id);
    }

    if (status) { conditions.push(`t.status = $${idx++}`); params.push(status); }
    if (priority) { conditions.push(`t.priority = $${idx++}`); params.push(priority); }
    if (categoryId) { conditions.push(`t.category_id = $${idx++}`); params.push(categoryId); }
    if (search) {
      conditions.push(`(t.description ILIKE $${idx} OR t.location ILIKE $${idx})`);
      params.push(`%${search}%`); idx++;
    }

    const where = conditions.length ? 'WHERE ' + conditions.join(' AND ') : '';

    const countRes = await pool.query(
      `SELECT COUNT(*) FROM ticket t ${where}`, params
    );
    const total = parseInt(countRes.rows[0].count);

    const { rows: ticketRows } = await pool.query(
      `SELECT t.id FROM ticket t ${where} ORDER BY t.created_at DESC LIMIT $${idx} OFFSET $${idx + 1}`,
      [...params, perPage, offset]
    );

    const tickets = [];
    for (const row of ticketRows) {
      const t = await buildTicketFull(row.id);
      if (t) tickets.push(ticketToDict(t));
    }

    res.json({ tickets, total, pages: Math.ceil(total / perPage), current_page: page, per_page: perPage });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/', requireAuth, loadUser, upload.array('attachments', 10), async (req, res) => {
  const user = req.user;
  const body = req.body;
  const location = (body.location || '').trim();
  const description = (body.description || '').trim();
  const priority = body.priority || 'medium';
  const categoryId = body.category_id && body.category_id !== '0' ? parseInt(body.category_id) : null;
  const assigneeIds = Array.isArray(body.assignees)
    ? body.assignees.map(Number)
    : (body.assignees ? [Number(body.assignees)] : []);

  if (!location || !description) {
    return res.status(400).json({ error: 'Location and description are required' });
  }

  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    const { rows } = await client.query(
      `INSERT INTO ticket (location, description, priority, status, created_by_id, category_id)
       VALUES ($1, $2, $3, 'open', $4, $5) RETURNING id`,
      [location, description, priority, user.id, categoryId]
    );
    const ticketId = rows[0].id;

    for (const aid of assigneeIds) {
      if (aid) {
        await client.query(
          `INSERT INTO ticket_assignees (ticket_id, user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING`,
          [ticketId, aid]
        );
      }
    }

    for (const file of (req.files || [])) {
      await client.query(
        `INSERT INTO attachment (filename, original_filename, file_size, content_type, ticket_id, uploaded_by_id)
         VALUES ($1, $2, $3, $4, $5, $6)`,
        [file.filename, file.originalname, file.size, file.mimetype, ticketId, user.id]
      );
    }

    await recordHistory(client, ticketId, user.id, 'created');
    await client.query('COMMIT');

    const ticket = await buildTicketFull(ticketId);
    notifyNewTicket(ticket).catch(() => {});
    res.status(201).json(ticketToDict(ticket));
  } catch (err) {
    await client.query('ROLLBACK');
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  } finally {
    client.release();
  }
});

router.get('/:id', requireAuth, loadUser, async (req, res) => {
  const user = req.user;
  const ticketId = parseInt(req.params.id);
  try {
    const ticket = await buildTicketFull(ticketId);
    if (!ticket) return res.status(404).json({ error: 'Ticket not found' });

    if (user.role === 'user' && ticket.created_by_id !== user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    if (user.role === 'intern') {
      const assignedIds = await getAssignedIds(user.id);
      if (!assignedIds.includes(ticketId) && ticket.created_by_id !== user.id) {
        return res.status(403).json({ error: 'Access denied' });
      }
    }

    res.json(ticketToDict(ticket, { includeComments: true, includeHistory: true, viewerRole: user.role }));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.put('/:id', requireAuth, loadUser, upload.array('attachments', 10), async (req, res) => {
  const user = req.user;
  const ticketId = parseInt(req.params.id);

  if (user.role === 'user') return res.status(403).json({ error: 'Access denied' });

  const client = await pool.connect();
  try {
    const { rows: ticketRows } = await client.query(`SELECT * FROM ticket WHERE id = $1`, [ticketId]);
    if (!ticketRows.length) return res.status(404).json({ error: 'Ticket not found' });
    const currentTicket = ticketRows[0];

    if (user.role === 'intern') {
      const assignedIds = await getAssignedIds(user.id);
      if (!assignedIds.includes(ticketId)) {
        return res.status(403).json({ error: 'Access denied — ticket not assigned to you' });
      }
    }

    const body = req.body || {};
    await client.query('BEGIN');

    if ('status' in body) {
      const newStatus = body.status;
      const allowedInternStatuses = new Set(['open', 'in_progress', 'resolved']);
      if (user.role === 'intern' && !allowedInternStatuses.has(newStatus)) {
        await client.query('ROLLBACK');
        return res.status(403).json({ error: `Interns cannot set status to ${newStatus}` });
      }
      if (currentTicket.status !== newStatus) {
        await recordHistory(client, ticketId, user.id, 'status changed', 'status', currentTicket.status, newStatus);
        await client.query(`UPDATE ticket SET status = $1, updated_at = NOW() WHERE id = $2`, [newStatus, ticketId]);
      }
    }

    if ('priority' in body && user.role === 'admin') {
      if (currentTicket.priority !== body.priority) {
        await recordHistory(client, ticketId, user.id, 'priority changed', 'priority', currentTicket.priority, body.priority);
        await client.query(`UPDATE ticket SET priority = $1 WHERE id = $2`, [body.priority, ticketId]);
      }
    }

    if ('category_id' in body && user.role === 'admin') {
      const catId = body.category_id && body.category_id !== '0' ? parseInt(body.category_id) : null;
      await client.query(`UPDATE ticket SET category_id = $1 WHERE id = $2`, [catId, ticketId]);
    }

    if ('assignees' in body && user.role === 'admin') {
      const assigneeIds = Array.isArray(body.assignees)
        ? body.assignees.map(Number)
        : (body.assignees ? [Number(body.assignees)] : []);
      await client.query(`DELETE FROM ticket_assignees WHERE ticket_id = $1`, [ticketId]);
      for (const aid of assigneeIds) {
        if (aid) {
          await client.query(
            `INSERT INTO ticket_assignees (ticket_id, user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING`,
            [ticketId, aid]
          );
        }
      }
      await recordHistory(client, ticketId, user.id, 'assignees updated');
    }

    for (const file of (req.files || [])) {
      await client.query(
        `INSERT INTO attachment (filename, original_filename, file_size, content_type, ticket_id, uploaded_by_id)
         VALUES ($1, $2, $3, $4, $5, $6)`,
        [file.filename, file.originalname, file.size, file.mimetype, ticketId, user.id]
      );
    }

    await client.query(`UPDATE ticket SET updated_at = NOW() WHERE id = $1`, [ticketId]);
    await client.query('COMMIT');

    const ticket = await buildTicketFull(ticketId);
    notifyTicketUpdated(ticket, user).catch(() => {});
    res.json(ticketToDict(ticket, { includeComments: true, includeHistory: true, viewerRole: user.role }));
  } catch (err) {
    await client.query('ROLLBACK');
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  } finally {
    client.release();
  }
});

router.delete('/:id', requireAuth, loadUser, async (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
  const { rowCount } = await pool.query(`DELETE FROM ticket WHERE id = $1`, [parseInt(req.params.id)]);
  if (!rowCount) return res.status(404).json({ error: 'Ticket not found' });
  res.json({ message: 'Ticket deleted' });
});

router.post('/:id/comment', requireAuth, loadUser, async (req, res) => {
  const user = req.user;
  const ticketId = parseInt(req.params.id);
  const { content, is_internal } = req.body || {};

  if (!content || !content.trim()) return res.status(400).json({ error: 'Comment content is required' });

  try {
    const { rows: ticketRows } = await pool.query(`SELECT * FROM ticket WHERE id = $1`, [ticketId]);
    if (!ticketRows.length) return res.status(404).json({ error: 'Ticket not found' });
    const ticket = ticketRows[0];

    if (user.role === 'user' && ticket.created_by_id !== user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    if (user.role === 'intern') {
      const assignedIds = await getAssignedIds(user.id);
      if (!assignedIds.includes(ticketId) && ticket.created_by_id !== user.id) {
        return res.status(403).json({ error: 'Access denied' });
      }
    }

    const isInternal = !!is_internal && ['admin', 'intern'].includes(user.role);
    const { rows } = await pool.query(
      `INSERT INTO comment (content, is_internal, ticket_id, author_id)
       VALUES ($1, $2, $3, $4) RETURNING *`,
      [content.trim(), isInternal, ticketId, user.id]
    );
    await pool.query(`UPDATE ticket SET updated_at = NOW() WHERE id = $1`, [ticketId]);

    const comment = rows[0];
    const { rows: authorRows } = await pool.query(`SELECT full_name, role FROM "user" WHERE id = $1`, [user.id]);
    comment.author_full_name = authorRows[0]?.full_name;
    comment.author_role = authorRows[0]?.role;

    const fullTicket = await buildTicketFull(ticketId);
    notifyNewComment(fullTicket, user).catch(() => {});

    res.status(201).json(commentToDict(comment));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/:id/escalate', requireAuth, loadUser, async (req, res) => {
  const user = req.user;
  if (!['intern', 'admin'].includes(user.role)) return res.status(403).json({ error: 'Access denied' });

  const ticketId = parseInt(req.params.id);
  const { reason, increase_priority } = req.body || {};

  if (!reason || reason.trim().length < 10) {
    return res.status(400).json({ error: 'Escalation reason must be at least 10 characters' });
  }

  const client = await pool.connect();
  try {
    const { rows } = await client.query(`SELECT * FROM ticket WHERE id = $1`, [ticketId]);
    if (!rows.length) return res.status(404).json({ error: 'Ticket not found' });
    const ticket = rows[0];

    if (user.role === 'intern') {
      const assignedIds = await getAssignedIds(user.id);
      if (!assignedIds.includes(ticketId)) {
        return res.status(403).json({ error: 'Access denied — ticket not assigned to you' });
      }
    }

    if (['closed', 'escalated'].includes(ticket.status)) {
      return res.status(400).json({ error: `Cannot escalate a ticket with status ${ticket.status}` });
    }

    await client.query('BEGIN');
    await recordHistory(client, ticketId, user.id, 'escalated', 'status', ticket.status, 'escalated');

    let updateQuery = `UPDATE ticket SET status = 'escalated', escalated_at = NOW(), escalated_by_id = $1, escalation_reason = $2, updated_at = NOW()`;
    const updateParams = [user.id, reason.trim()];
    if (increase_priority) {
      updateQuery += `, priority = 'urgent'`;
    }
    updateQuery += ` WHERE id = $${updateParams.length + 1}`;
    updateParams.push(ticketId);
    await client.query(updateQuery, updateParams);
    await client.query('COMMIT');

    const updated = await buildTicketFull(ticketId);
    res.json(ticketToDict(updated));
  } catch (err) {
    await client.query('ROLLBACK');
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  } finally {
    client.release();
  }
});

router.post('/:id/close', requireAuth, loadUser, async (req, res) => {
  const user = req.user;
  const ticketId = parseInt(req.params.id);

  const client = await pool.connect();
  try {
    const { rows } = await client.query(`SELECT * FROM ticket WHERE id = $1`, [ticketId]);
    if (!rows.length) return res.status(404).json({ error: 'Ticket not found' });
    const ticket = rows[0];

    if (user.role !== 'admin' && ticket.created_by_id !== user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    await client.query('BEGIN');
    await client.query(
      `UPDATE ticket SET status = 'closed', closed_at = NOW(), closed_by_id = $1, updated_at = NOW() WHERE id = $2`,
      [user.id, ticketId]
    );
    await recordHistory(client, ticketId, user.id, 'closed');
    await client.query('COMMIT');

    const updated = await buildTicketFull(ticketId);
    notifyTicketClosed(updated, user).catch(() => {});
    res.json(ticketToDict(updated));
  } catch (err) {
    await client.query('ROLLBACK');
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  } finally {
    client.release();
  }
});

module.exports = router;
module.exports.buildTicketFull = buildTicketFull;
