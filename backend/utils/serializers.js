function userToDict(u) {
  return {
    id: u.id,
    username: u.username,
    email: u.email,
    full_name: u.full_name,
    role: u.role,
    is_active: u.is_active,
    is_verified: u.is_verified,
    is_approved: u.is_approved,
    phone_number: u.phone_number,
    created_at: u.created_at ? u.created_at.toISOString() : null,
    approved_at: u.approved_at ? u.approved_at.toISOString() : null,
  };
}

function attachmentToDict(a) {
  return {
    id: a.id,
    original_filename: a.original_filename,
    file_size: a.file_size,
    content_type: a.content_type,
    created_at: a.created_at ? a.created_at.toISOString() : null,
    url: `/api/v1/attachments/${a.filename}`,
  };
}

function commentToDict(c) {
  return {
    id: c.id,
    content: c.content,
    is_internal: c.is_internal,
    created_at: c.created_at ? c.created_at.toISOString() : null,
    author: c.author_id ? {
      id: c.author_id,
      full_name: c.author_full_name || null,
      role: c.author_role || null,
    } : null,
  };
}

function historyToDict(h) {
  return {
    id: h.id,
    action: h.action,
    field_changed: h.field_changed,
    old_value: h.old_value,
    new_value: h.new_value,
    timestamp: h.timestamp ? h.timestamp.toISOString() : null,
    user: h.user_id ? { id: h.user_id, full_name: h.user_full_name || null } : null,
  };
}

function ticketToDict(t, { includeComments = false, includeHistory = false, viewerRole = null } = {}) {
  const data = {
    id: t.id,
    created_by_id: t.created_by_id,
    location: t.location,
    description: t.description,
    status: t.status,
    priority: t.priority,
    created_at: t.created_at ? t.created_at.toISOString() : null,
    updated_at: t.updated_at ? t.updated_at.toISOString() : null,
    closed_at: t.closed_at ? t.closed_at.toISOString() : null,
    due_date: t.due_date ? t.due_date.toISOString() : null,
    escalated_at: t.escalated_at ? t.escalated_at.toISOString() : null,
    escalation_reason: t.escalation_reason || null,
    category: t.category_id ? { id: t.category_id, name: t.category_name || null } : null,
    creator: t.created_by_id ? {
      id: t.created_by_id,
      full_name: t.creator_full_name || null,
      username: t.creator_username || null,
    } : null,
    assignees: t.assignees || [],
    closed_by: t.closed_by_id ? { id: t.closed_by_id, full_name: t.closed_by_full_name || null } : null,
    escalated_by: t.escalated_by_id ? { id: t.escalated_by_id, full_name: t.escalated_by_full_name || null } : null,
    attachments: t.attachments || [],
    comment_count: t.comment_count || 0,
  };
  if (includeComments) {
    let comments = t.comments || [];
    if (viewerRole === 'user') {
      comments = comments.filter(c => !c.is_internal);
    }
    data.comments = comments;
  }
  if (includeHistory) {
    data.history = t.history || [];
  }
  return data;
}

function notificationToDict(n) {
  return {
    id: n.id,
    type: n.type,
    title: n.title,
    message: n.message,
    is_read: n.is_read,
    created_at: n.created_at ? n.created_at.toISOString() : null,
    ticket_id: n.ticket_id,
  };
}

module.exports = { userToDict, attachmentToDict, commentToDict, historyToDict, ticketToDict, notificationToDict };
