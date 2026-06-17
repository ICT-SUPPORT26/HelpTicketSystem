import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'
import { StatusBadge, PriorityBadge } from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import StatusTracker from '../components/common/StatusTracker'
import toast from 'react-hot-toast'
import { format, formatDistanceToNow } from 'date-fns'

function getInitials(name) {
  return (name || 'U').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

export default function TicketDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [ticket, setTicket] = useState(null)
  const [loading, setLoading] = useState(true)
  const [commentText, setCommentText] = useState('')
  const [isInternal, setIsInternal] = useState(false)
  const [submittingComment, setSubmittingComment] = useState(false)
  const [escalateReason, setEscalateReason] = useState('')
  const [showEscalate, setShowEscalate] = useState(false)
  const [updateStatus, setUpdateStatus] = useState('')
  const [categories, setCategories] = useState([])
  const [staff, setStaff] = useState([])
  const [showUpdate, setShowUpdate] = useState(false)
  const [updateForm, setUpdateForm] = useState({ status: '', priority: '', category_id: '', assignees: [] })

  useEffect(() => {
    fetchTicket()
    client.get('/categories').then(r => setCategories(r.data)).catch(() => {})
    client.get('/users/staff').then(r => setStaff(r.data)).catch(() => {})
  }, [id])

  async function fetchTicket() {
    setLoading(true)
    try {
      const res = await client.get(`/tickets/${id}`)
      setTicket(res.data)
      setUpdateForm({
        status: res.data.status,
        priority: res.data.priority,
        category_id: res.data.category?.id || '',
        assignees: res.data.assignees?.map(a => a.id) || [],
      })
    } catch { navigate('/tickets') }
    setLoading(false)
  }

  async function submitComment(e) {
    e.preventDefault()
    if (!commentText.trim()) return
    setSubmittingComment(true)
    try {
      const res = await client.post(`/tickets/${id}/comment`, { content: commentText, is_internal: isInternal })
      setTicket(t => ({ ...t, comments: [...(t.comments || []), res.data] }))
      setCommentText('')
      toast.success('Comment added')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to add comment')
    }
    setSubmittingComment(false)
  }

  async function handleEscalate(e) {
    e.preventDefault()
    try {
      const res = await client.post(`/tickets/${id}/escalate`, { reason: escalateReason })
      setTicket(res.data)
      setShowEscalate(false)
      setEscalateReason('')
      toast.success('Ticket escalated')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to escalate')
    }
  }

  async function handleClose() {
    if (!confirm('Close this ticket?')) return
    try {
      const res = await client.post(`/tickets/${id}/close`)
      setTicket(res.data)
      toast.success('Ticket closed')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to close')
    }
  }

  async function handleDelete() {
    if (!confirm('Permanently delete this ticket?')) return
    try {
      await client.delete(`/tickets/${id}`)
      toast.success('Ticket deleted')
      navigate('/tickets')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete')
    }
  }

  async function handleUpdate(e) {
    e.preventDefault()
    try {
      const res = await client.put(`/tickets/${id}`, updateForm)
      setTicket(res.data)
      setShowUpdate(false)
      toast.success('Ticket updated')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Update failed')
    }
  }

  if (loading) return <LoadingSpinner size="lg" text="Loading ticket…" />
  if (!ticket) return null

  const canComment = user.role !== 'user' || ticket.created_by_id === user.id || ticket.creator?.id === user.id
  const canEscalate = user.role === 'intern' && !['closed', 'escalated'].includes(ticket.status)
  const canUpdate = user.role === 'admin' || (user.role === 'intern' && ticket.assignees?.some(a => a.id === user.id))
  const canClose = user.role === 'admin' || ticket.creator?.id === user.id
  const canDelete = user.role === 'admin'

  return (
    <div>
      <div className="page-header">
        <div className="flex gap-8">
          <button className="btn btn-outline btn-sm" onClick={() => navigate('/tickets')}>
            <i className="bi bi-arrow-left" /> Back
          </button>
          <div>
            <h1 className="page-title">Ticket #{ticket.id}</h1>
            <p className="page-subtitle">{ticket.location}</p>
          </div>
        </div>
        <div className="flex gap-8">
          {canEscalate && <button className="btn btn-warning btn-sm" onClick={() => setShowEscalate(true)}><i className="bi bi-exclamation-triangle" /> Escalate</button>}
          {canUpdate && <button className="btn btn-secondary btn-sm" onClick={() => setShowUpdate(s => !s)}><i className="bi bi-pencil" /> Update</button>}
          {canClose && ticket.status !== 'closed' && <button className="btn btn-success btn-sm" onClick={handleClose}><i className="bi bi-check-circle" /> Close</button>}
          {canDelete && <button className="btn btn-danger btn-sm" onClick={handleDelete}><i className="bi bi-trash" /> Delete</button>}
        </div>
      </div>

      {/* Update Panel */}
      {showUpdate && (
        <div className="card mb-16">
          <div className="card-header"><h3>Update Ticket</h3></div>
          <div className="card-body">
            <form onSubmit={handleUpdate}>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Status</label>
                  <select className="form-control" value={updateForm.status} onChange={e => setUpdateForm(f => ({ ...f, status: e.target.value }))}>
                    {['open','in_progress','resolved','closed','escalated'].map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
                  </select>
                </div>
                {user.role === 'admin' && (
                  <div className="form-group">
                    <label className="form-label">Priority</label>
                    <select className="form-control" value={updateForm.priority} onChange={e => setUpdateForm(f => ({ ...f, priority: e.target.value }))}>
                      {['low','medium','high','urgent'].map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                )}
              </div>
              {user.role === 'admin' && (
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Category</label>
                    <select className="form-control" value={updateForm.category_id} onChange={e => setUpdateForm(f => ({ ...f, category_id: e.target.value }))}>
                      <option value="">No Category</option>
                      {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Assignees</label>
                    <select className="form-control" multiple value={updateForm.assignees.map(String)}
                      onChange={e => setUpdateForm(f => ({ ...f, assignees: Array.from(e.target.selectedOptions, o => parseInt(o.value)) }))}>
                      {staff.map(s => <option key={s.id} value={s.id}>{s.full_name} ({s.role})</option>)}
                    </select>
                  </div>
                </div>
              )}
              <div className="flex gap-8">
                <button type="submit" className="btn btn-primary btn-sm">Save Changes</button>
                <button type="button" className="btn btn-outline btn-sm" onClick={() => setShowUpdate(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Escalate Modal */}
      {showEscalate && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowEscalate(false)}>
          <div className="modal">
            <div className="modal-header">
              <h3>Escalate Ticket</h3>
              <button className="btn-icon" onClick={() => setShowEscalate(false)}><i className="bi bi-x-lg" /></button>
            </div>
            <form onSubmit={handleEscalate}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Escalation Reason (min 10 characters)</label>
                  <textarea className="form-control" value={escalateReason} onChange={e => setEscalateReason(e.target.value)} required minLength={10} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-outline btn-sm" onClick={() => setShowEscalate(false)}>Cancel</button>
                <button type="submit" className="btn btn-warning btn-sm">Escalate</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20 }}>
        <div>
          {/* Main Info */}
          <div className="card mb-16">
            <div className="card-header">
              <h3>Ticket Details</h3>
              <div className="flex gap-8">
                <StatusBadge status={ticket.status} />
                <PriorityBadge priority={ticket.priority} />
              </div>
            </div>
            <div className="card-body">
              <div style={{ marginBottom: 16 }}>
                <div className="form-label">Location</div>
                <div style={{ fontWeight: 500 }}>{ticket.location}</div>
              </div>
              <div style={{ marginBottom: 16 }}>
                <div className="form-label">Description</div>
                <div style={{ lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{ticket.description}</div>
              </div>
              {ticket.escalation_reason && (
                <div className="alert alert-warning">
                  <strong>Escalation Reason:</strong> {ticket.escalation_reason}
                </div>
              )}
            </div>
          </div>

          {/* Attachments */}
          {ticket.attachments?.length > 0 && (
            <div className="card mb-16">
              <div className="card-header"><h3>Attachments</h3></div>
              <div className="card-body">
                {ticket.attachments.map(a => (
                  <button
                    key={a.id}
                    className="flex gap-8"
                    style={{ padding: '8px 0', borderBottom: '1px solid #f3f4f6', color: '#3b82f6', background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left' }}
                    onClick={async () => {
                      try {
                        const res = await client.get(a.url, { responseType: 'blob' })
                        const blobUrl = URL.createObjectURL(res.data)
                        const link = document.createElement('a')
                        link.href = blobUrl
                        link.download = a.original_filename
                        document.body.appendChild(link)
                        link.click()
                        document.body.removeChild(link)
                        URL.revokeObjectURL(blobUrl)
                      } catch {
                        toast.error('Failed to download attachment')
                      }
                    }}
                  >
                    <i className="bi bi-paperclip" />
                    <span>{a.original_filename}</span>
                    <span style={{ color: '#9ca3af', fontSize: 12 }}>({Math.round(a.file_size / 1024)}KB)</span>
                    <i className="bi bi-download" style={{ marginLeft: 'auto', fontSize: 12 }} />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Comments */}
          <div className="card mb-16">
            <div className="card-header"><h3>Comments ({ticket.comments?.length || 0})</h3></div>
            <div className="card-body">
              {ticket.comments?.length === 0 && <div style={{ color: '#9ca3af', fontSize: 13 }}>No comments yet.</div>}
              {ticket.comments?.filter(c => !c.is_internal || user.role !== 'user').map(c => (
                <div key={c.id} className="comment">
                  <div className="avatar avatar-sm">{getInitials(c.author?.full_name)}</div>
                  <div className={`comment-body ${c.is_internal ? 'internal' : ''}`}>
                    <div className="comment-meta">
                      <span className="comment-author">{c.author?.full_name || 'Unknown'}</span>
                      {c.is_internal && <span className="badge" style={{ background: '#fffbeb', color: '#b45309', fontSize: 10 }}>Internal</span>}
                      <span className="comment-time">{formatDistanceToNow(new Date(c.created_at), { addSuffix: true })}</span>
                    </div>
                    <div className="comment-content">{c.content}</div>
                  </div>
                </div>
              ))}

              {canComment && ticket.status !== 'closed' && (
                <form onSubmit={submitComment} style={{ marginTop: 16 }}>
                  <textarea className="form-control" placeholder="Add a comment…" value={commentText}
                    onChange={e => setCommentText(e.target.value)} style={{ marginBottom: 8 }} />
                  {user.role !== 'user' && (
                    <label className="flex gap-8" style={{ marginBottom: 8, cursor: 'pointer' }}>
                      <input type="checkbox" checked={isInternal} onChange={e => setIsInternal(e.target.checked)} />
                      <span style={{ fontSize: 13 }}>Internal comment (only visible to staff)</span>
                    </label>
                  )}
                  <button type="submit" className="btn btn-primary btn-sm" disabled={submittingComment}>
                    {submittingComment ? 'Posting…' : 'Post Comment'}
                  </button>
                </form>
              )}
            </div>
          </div>

          {/* Status Tracker + Activity Timeline */}
          <StatusTracker ticket={ticket} />
        </div>

        {/* Sidebar Info */}
        <div>
          <div className="card mb-16">
            <div className="card-header"><h3>Info</h3></div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[
                { label: 'Status', value: <StatusBadge status={ticket.status} /> },
                { label: 'Priority', value: <PriorityBadge priority={ticket.priority} /> },
                { label: 'Category', value: ticket.category?.name || '—' },
                { label: 'Created by', value: ticket.creator?.full_name || '—' },
                { label: 'Created', value: ticket.created_at ? format(new Date(ticket.created_at), 'MMM d, yyyy HH:mm') : '—' },
                { label: 'Updated', value: ticket.updated_at ? format(new Date(ticket.updated_at), 'MMM d, yyyy HH:mm') : '—' },
                ticket.closed_at && { label: 'Closed', value: format(new Date(ticket.closed_at), 'MMM d, yyyy HH:mm') },
              ].filter(Boolean).map(row => (
                <div key={row.label}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>{row.label}</div>
                  <div style={{ fontSize: 14 }}>{row.value}</div>
                </div>
              ))}
            </div>
          </div>

          {ticket.assignees?.length > 0 && (
            <div className="card">
              <div className="card-header"><h3>Assignees</h3></div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {ticket.assignees.map(a => (
                  <div key={a.id} className="flex gap-8">
                    <div className="avatar avatar-sm">{getInitials(a.full_name)}</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{a.full_name}</div>
                      <div style={{ fontSize: 11, color: '#9ca3af' }}>{a.username}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
