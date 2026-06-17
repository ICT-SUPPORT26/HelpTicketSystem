import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import client from '../api/client'
import { StatusBadge, PriorityBadge } from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import DashboardCard from '../components/common/DashboardCard'
import Modal from '../components/common/Modal'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [pendingInterns, setPendingInterns] = useState([])
  const [loading, setLoading] = useState(true)
  const [newCategory, setNewCategory] = useState('')
  const [addingCategory, setAddingCategory] = useState(false)

  const [selectedCard, setSelectedCard] = useState(null)
  const [modalTickets, setModalTickets] = useState([])
  const [loadingTickets, setLoadingTickets] = useState(false)

  useEffect(() => {
    Promise.all([
      client.get('/dashboard/stats'),
      client.get('/users/interns/pending'),
    ]).then(([statsRes, internsRes]) => {
      setStats(statsRes.data)
      setPendingInterns(internsRes.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const openModal = useCallback(async (card) => {
    setSelectedCard(card)
    setModalTickets([])

    if (card.label === 'Pending Approvals') return

    setLoadingTickets(true)
    try {
      const statusParam = {
        'Total Tickets': '',
        'Open': 'open',
        'In Progress': 'in_progress',
        'Resolved': 'resolved',
        'Escalated': 'escalated',
      }[card.label] ?? ''

      const url = statusParam
        ? `/tickets?status=${statusParam}&per_page=6`
        : '/tickets?per_page=6'

      const r = await client.get(url)
      setModalTickets(r.data?.tickets ?? r.data?.items ?? [])
    } catch {
      setModalTickets([])
    } finally {
      setLoadingTickets(false)
    }
  }, [])

  const closeModal = useCallback(() => {
    setSelectedCard(null)
    setModalTickets([])
  }, [])

  async function approveIntern(id) {
    try {
      await client.post(`/users/${id}/approve`)
      setPendingInterns(i => i.filter(u => u.id !== id))
      toast.success('Intern approved')
    } catch { toast.error('Failed to approve') }
  }

  async function handleAddCategory(e) {
    e.preventDefault()
    if (!newCategory.trim()) return
    setAddingCategory(true)
    try {
      await client.post('/categories', { name: newCategory.trim() })
      setNewCategory('')
      toast.success('Category added')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to add category')
    }
    setAddingCategory(false)
  }

  if (loading) return <LoadingSpinner size="lg" text="Loading admin dashboard…" />

  const statCards = [
    { label: 'Total Tickets',     value: stats?.total ?? 0,        icon: 'bi-ticket-detailed-fill',      color: 'blue',   link: '/tickets' },
    { label: 'Open',              value: stats?.open ?? 0,          icon: 'bi-folder2-open',              color: 'yellow', link: '/tickets?status=open' },
    { label: 'In Progress',       value: stats?.in_progress ?? 0,   icon: 'bi-arrow-repeat',              color: 'cyan',   link: '/tickets?status=in_progress' },
    { label: 'Escalated',         value: stats?.escalated ?? 0,     icon: 'bi-exclamation-triangle-fill', color: 'red',    link: '/tickets?status=escalated' },
    { label: 'Resolved',          value: stats?.resolved ?? 0,      icon: 'bi-check-circle-fill',         color: 'green',  link: '/tickets?status=resolved' },
    { label: 'Pending Approvals', value: pendingInterns.length,      icon: 'bi-person-check-fill',         color: 'gray',   link: '/admin/users' },
  ]

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Admin Dashboard</h1>
          <p className="page-subtitle">System overview and management</p>
        </div>
        <div className="flex gap-8">
          <Link to="/admin/users" className="btn btn-secondary btn-sm"><i className="bi bi-people" /> Manage Users</Link>
          <Link to="/tickets/new" className="btn btn-primary btn-sm"><i className="bi bi-plus-circle" /> New Ticket</Link>
        </div>
      </div>

      <div className="stats-grid">
        {statCards.map(c => (
          <DashboardCard key={c.label} card={c} onClick={openModal} />
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 20 }}>
        <div>
          {/* Recent Tickets */}
          <div className="card mb-16">
            <div className="card-header">
              <h3><i className="bi bi-clock-history" style={{ marginRight: 8 }} />Recent Tickets</h3>
              <Link to="/tickets" className="btn btn-secondary btn-sm">View All</Link>
            </div>
            <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
              {!stats?.recent_tickets?.length ? (
                <div className="empty-state"><i className="bi bi-ticket" /><p>No recent tickets</p></div>
              ) : (
                <table>
                  <thead>
                    <tr><th>#</th><th>Location</th><th>Status</th><th>Priority</th><th>Created</th></tr>
                  </thead>
                  <tbody>
                    {stats.recent_tickets.map(t => (
                      <tr key={t.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/tickets/${t.id}`)}>
                        <td style={{ color: '#6b7280', fontSize: 12 }}>#{t.id}</td>
                        <td>
                          <div style={{ fontWeight: 500 }}>{t.location}</div>
                          <div style={{ fontSize: 12, color: '#6b7280' }}>{t.description?.slice(0, 50)}…</div>
                        </td>
                        <td><StatusBadge status={t.status} /></td>
                        <td><PriorityBadge priority={t.priority} /></td>
                        <td style={{ fontSize: 12, color: '#6b7280' }}>{t.created_at ? format(new Date(t.created_at), 'MMM d') : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <div className="card-header"><h3>Quick Actions</h3></div>
            <div className="card-body" style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <Link to="/tickets?status=open" className="btn btn-outline"><i className="bi bi-folder2-open" /> View Open Tickets</Link>
              <Link to="/tickets?status=escalated" className="btn btn-warning"><i className="bi bi-exclamation-triangle" /> Escalated Tickets</Link>
              <Link to="/reports" className="btn btn-outline"><i className="bi bi-bar-chart" /> View Reports</Link>
              <Link to="/analytics" className="btn btn-outline"><i className="bi bi-graph-up" /> Analytics</Link>
            </div>
          </div>
        </div>

        <div>
          {/* Pending Interns */}
          <div className="card mb-16">
            <div className="card-header">
              <h3>Pending Approvals</h3>
              {pendingInterns.length > 0 && <span className="notif-badge">{pendingInterns.length}</span>}
            </div>
            <div className="card-body" style={{ padding: pendingInterns.length ? 0 : 20 }}>
              {pendingInterns.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>No pending approvals</div>
              ) : (
                pendingInterns.map(u => (
                  <div key={u.id} style={{ padding: '12px 16px', borderBottom: '1px solid #f3f4f6' }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{u.full_name}</div>
                    <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>@{u.username} · {u.email}</div>
                    <button className="btn btn-success btn-sm" onClick={() => approveIntern(u.id)}>
                      <i className="bi bi-check-circle" /> Approve
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Add Category */}
          <div className="card">
            <div className="card-header"><h3>Add Category</h3></div>
            <div className="card-body">
              <form onSubmit={handleAddCategory}>
                <div className="form-group">
                  <input className="form-control" placeholder="Category name…" value={newCategory}
                    onChange={e => setNewCategory(e.target.value)} />
                </div>
                <button type="submit" className="btn btn-primary btn-sm" disabled={addingCategory}>
                  {addingCategory ? 'Adding…' : <><i className="bi bi-plus" /> Add Category</>}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>

      <Modal
        isOpen={!!selectedCard}
        onClose={closeModal}
        card={selectedCard}
        tickets={modalTickets}
        loadingTickets={loadingTickets}
      />
    </div>
  )
}
