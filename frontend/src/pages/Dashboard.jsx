import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'
import { StatusBadge, PriorityBadge } from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import { format } from 'date-fns'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    client.get('/dashboard/stats').then(r => { setStats(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner size="lg" text="Loading dashboard…" />

  const cards = [
    { label: 'Total Tickets', value: stats?.total ?? 0, icon: 'bi-ticket-detailed-fill', color: 'blue', link: '/tickets' },
    { label: 'Open', value: stats?.open ?? 0, icon: 'bi-folder2-open', color: 'yellow', link: '/tickets?status=open' },
    { label: 'In Progress', value: stats?.in_progress ?? 0, icon: 'bi-arrow-repeat', color: 'cyan', link: '/tickets?status=in_progress' },
    { label: 'Resolved', value: stats?.resolved ?? 0, icon: 'bi-check-circle-fill', color: 'green', link: '/tickets?status=resolved' },
  ]

  if (user?.role === 'admin') {
    cards.push({ label: 'Escalated', value: stats?.escalated ?? 0, icon: 'bi-exclamation-triangle-fill', color: 'red', link: '/tickets?status=escalated' })
    cards.push({ label: 'Pending Approvals', value: stats?.pending_users ?? 0, icon: 'bi-person-check-fill', color: 'gray', link: '/admin/users' })
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">👋 Welcome back, {user?.full_name?.split(' ')[0]}!</h1>
          <p className="page-subtitle">Here's what's happening with your tickets today.</p>
        </div>
        <Link to="/tickets/new" className="btn btn-primary">
          <i className="bi bi-plus-circle" /> New Ticket
        </Link>
      </div>

      <div className="stats-grid">
        {cards.map(c => (
          <div key={c.label} className="stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate(c.link)}>
            <div className={`stat-icon ${c.color}`}><i className={`bi ${c.icon}`} /></div>
            <div>
              <div className="stat-number">{c.value}</div>
              <div className="stat-label">{c.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <h3><i className="bi bi-clock-history" style={{ marginRight: 8 }} />Recent Tickets</h3>
          <Link to="/tickets" className="btn btn-secondary btn-sm">View All</Link>
        </div>
        <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
          {!stats?.recent_tickets?.length ? (
            <div className="empty-state">
              <i className="bi bi-ticket" />
              <p>No tickets yet. <Link to="/tickets/new">Create your first ticket</Link></p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Location / Description</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_tickets.map(t => (
                  <tr key={t.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/tickets/${t.id}`)}>
                    <td style={{ color: '#6b7280', fontSize: 12 }}>#{t.id}</td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{t.location}</div>
                      <div style={{ fontSize: 12, color: '#6b7280' }}>{t.description?.slice(0, 60)}…</div>
                    </td>
                    <td><StatusBadge status={t.status} /></td>
                    <td><PriorityBadge priority={t.priority} /></td>
                    <td style={{ fontSize: 12, color: '#6b7280' }}>
                      {t.created_at ? format(new Date(t.created_at), 'MMM d, yyyy') : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
