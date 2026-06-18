const pool = require('../db/pool');

async function createNotification(userId, ticketId, type, title, message) {
  try {
    await pool.query(
      `INSERT INTO notification (user_id, ticket_id, type, title, message, is_read, created_at)
       VALUES ($1, $2, $3, $4, $5, FALSE, NOW())`,
      [userId, ticketId, type, title, message]
    );
  } catch (err) {
    console.error('Error creating notification:', err.message);
  }
}

async function notifyNewTicket(ticket) {
  try {
    const assignees = ticket.assignees || [];
    if (assignees.length === 0) {
      const { rows: admins } = await pool.query(
        `SELECT id FROM "user" WHERE role = 'admin' AND is_active = TRUE`
      );
      for (const admin of admins) {
        await createNotification(
          admin.id, ticket.id, 'new_ticket',
          `New Unassigned Ticket: #${ticket.id}`,
          `A new ticket has been created that needs assignment.\n\nLocation: ${ticket.location}\nPriority: ${ticket.priority}\nCreated by: ${ticket.creator_full_name || 'Unknown'}`
        );
      }
    }
    for (const assignee of assignees) {
      await createNotification(
        assignee.id, ticket.id, 'ticket_assigned',
        `New Ticket Assigned: #${ticket.id}`,
        `A new ticket has been assigned to you.\n\nLocation: ${ticket.location}\nPriority: ${ticket.priority}\nCreated by: ${ticket.creator_full_name || 'Unknown'}`
      );
    }
  } catch (err) {
    console.error('notifyNewTicket error:', err.message);
  }
}

async function notifyTicketUpdated(ticket, updatedBy) {
  try {
    if (ticket.created_by_id && ticket.created_by_id !== updatedBy.id) {
      await createNotification(
        ticket.created_by_id, ticket.id, 'ticket_updated',
        `Ticket Updated: #${ticket.id}`,
        `Your ticket has been updated by ${updatedBy.full_name}.\n\nLocation: ${ticket.location}\nStatus: ${ticket.status}\nPriority: ${ticket.priority}`
      );
    }
    const assignees = ticket.assignees || [];
    for (const assignee of assignees) {
      if (assignee.id !== updatedBy.id) {
        await createNotification(
          assignee.id, ticket.id, 'ticket_updated',
          `Assigned Ticket Updated: #${ticket.id}`,
          `A ticket assigned to you has been updated by ${updatedBy.full_name}.\n\nLocation: ${ticket.location}\nStatus: ${ticket.status}\nPriority: ${ticket.priority}`
        );
      }
    }
  } catch (err) {
    console.error('notifyTicketUpdated error:', err.message);
  }
}

async function notifyNewComment(ticket, commentAuthor) {
  try {
    if (ticket.created_by_id && ticket.created_by_id !== commentAuthor.id) {
      await createNotification(
        ticket.created_by_id, ticket.id, 'new_comment',
        `New Comment on Ticket #${ticket.id}`,
        `${commentAuthor.full_name} added a comment to your ticket.\n\nLocation: ${ticket.location}`
      );
    }
    const assignees = ticket.assignees || [];
    for (const assignee of assignees) {
      if (assignee.id !== commentAuthor.id) {
        await createNotification(
          assignee.id, ticket.id, 'new_comment',
          `New Comment on Assigned Ticket #${ticket.id}`,
          `${commentAuthor.full_name} added a comment to a ticket assigned to you.\n\nLocation: ${ticket.location}`
        );
      }
    }
  } catch (err) {
    console.error('notifyNewComment error:', err.message);
  }
}

async function notifyTicketClosed(ticket, closedBy) {
  try {
    if (ticket.created_by_id && ticket.created_by_id !== closedBy.id) {
      await createNotification(
        ticket.created_by_id, ticket.id, 'ticket_closed',
        `Ticket Closed: #${ticket.id}`,
        `Your ticket has been closed by ${closedBy.full_name}.\n\nLocation: ${ticket.location}`
      );
    }
    const assignees = ticket.assignees || [];
    for (const assignee of assignees) {
      if (assignee.id !== closedBy.id) {
        await createNotification(
          assignee.id, ticket.id, 'ticket_closed',
          `Assigned Ticket Closed: #${ticket.id}`,
          `A ticket assigned to you has been closed by ${closedBy.full_name}.\n\nLocation: ${ticket.location}`
        );
      }
    }
  } catch (err) {
    console.error('notifyTicketClosed error:', err.message);
  }
}

module.exports = { createNotification, notifyNewTicket, notifyTicketUpdated, notifyNewComment, notifyTicketClosed };
