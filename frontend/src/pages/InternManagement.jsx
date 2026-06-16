import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import client from '../api/client'
import { RoleBadge } from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

function getInitials(name) {
  return (name || 'U').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

function ProgressBar({ value, max, color = '#3b82f6' }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div style={{ background: '#f3f4f6', borderRadius: 999, height: 8, overflow: 'hidden', width: '100%' }}>
      <div style={{ width: `${pct}%`, background: color, height: '100%', borderRadius: 999, transition: 'width 0.6s ease' }} />
    </div>
  )
}

export default function InternManagement() {
  const navigate = useNavigate()
  const [interns, setInterns] = useState([])
  const [pending, setPending] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      client.get('/users/interns/stats'),
      client.get('/users/interns/pending'),
    ]).then(([statsRes, pendingRes]) => {
      setInterns(statsRes.data)
      setPending(pendingRes.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  async function approveIntern(id) {
    try {
      await client.post(`/users/${id}/approve`)
      setPending(p => p.filter(u => u.id !== id))
      // Refresh intern stats to show newly approved intern
      const res = await client.get('/users/interns/stats')
      setInterns(res.data)
      toast.success('Intern approved')
    } catch { toast.error('Failed to approve') }
  }

  async function toggleStatus(intern) {
    try {
      const res = await client.post(`/users/${intern.id}/toggle-status`)
      setInterns(prev => prev.map(i => i.id === intern.id ? { ...i, is_active: res.data.is_active } : i))
      toast.success(`${intern.full_name} ${res.data.is_active ? 'activated' : 'deactivated'}`)
    } catch { toast.error('Failed') }
  }

  if (loading) return <LoadingSpinner size="lg" text="Loading intern management…" />

  const activeInterns = interns.filter(i => i.is_active && i.is_approved)
  const inactiveInterns = interns.filter(i => !i.is_active || !i.is_approved)

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Intern Management</h1>
          <p className="page-subtitle">
            {activeInterns.length} active intern{activeInterns.length !== 1 ? 's' : ''}
            {pending.length > 0 && ` · ${pending.length} pending approval`}
          </p>
        </div>
        <div className="flex gap-8">
          <Link to="/admin/users" className="btn btn-outline btn-sm">
            <i className="bi bi-people" /> All Users
          </Link>
          <Link to="/analytics" className="btn btn-secondary btn-sm">
            <i className="bi bi-graph-up" /> Analytics
          </Link>
        </div>
      </div>

      {/* Pending Approvals */}
      {pending.length > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <h3><i className="bi bi-person-check" style={{ marginRight: 8 }} />Pending Approvals</h3>
            <span className="notif-badge">{pending.length}</span>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            {pending.map(u => (
              <div key={u.id} className="flex-between" style={{ padding: '12px 20px', borderBottom: '1px solid #f3f4f6' }}>
                <div className="flex gap-8">
                  <div className="avatar">{getInitials(u.full_name)}</div>
                  <div>
                    <div style={{ fontWeight: 600 }}>{u.full_name}</div>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>@{u.username} · {u.email}</div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>
                      Applied {u.created_at ? format(new Date(u.created_at), 'MMM d, yyyy') : '—'}
                    </div>
                  </div>
                </div>
                <button className="btn btn-success btn-sm" onClick={() => approveIntern(u.id)}>
                  <i className="bi bi-check-circle" /> Approve
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance Overview — Active Interns */}
      <div className="card mb-24">
        <div className="card-header">
          <h3><i className="bi bi-bar-chart" style={{ marginRight: 8 }} />Performance Overview</h3>
          <span style={{ fontSize: 12, color: '#6b7280' }}>{activeInterns.length} active interns</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {activeInterns.length === 0 ? (
            <div className="empty-state" style={{ padding: 48 }}>
              <i className="bi bi-people" />
              <p>No active interns yet. Approve pending applications above.</p>
            </div>
          ) : (
            activeInterns.map(intern => {
              const total = intern.total_assigned
              const resolvedPct = total > 0 ? Math.round((intern.resolved / total) * 100) : 0
              return (
                <div key={intern.id} style={{ padding: '20px 24px', borderBottom: '1px solid #f3f4f6' }}>
                  <div className="flex-between" style={{ marginBottom: 12 }}>
                    <div className="flex gap-8">
                      <div className="avatar">{getInitials(intern.full_name)}</div>
                      <div>
                        <div style={{ fontWeight: 600 }}>{intern.full_name}</div>
                        <div style={{ fontSize: 12, color: '#6b7280' }}>@{intern.username} · {intern.email}</div>
                      </div>
                    </div>
                    <div className="flex gap-8">
                      <button className="btn btn-outline btn-sm" onClick={() => navigate(`/tickets?status=open`)}>
                        View Tickets
                      </button>
                      <button className="btn btn-secondary btn-sm" onClick={() => toggleStatus(intern)}>
                        {intern.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
                  </div>

                  {/* Ticket Stats */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 12 }}>
                    {[
                      { label: 'Total', value: total, color: '#6b7280' },
                      { label: 'Open', value: intern.open, color: '#f59e0b' },
                      { label: 'In Progress', value: intern.in_progress, color: '#06b6d4' },
                      { label: 'Resolved', value: intern.resolved, color: '#10b981' },
                      { label: 'Escalated', value: intern.escalated, color: '#ef4444' },
                    ].map(s => (
                      <div key={s.label} style={{ textAlign: 'center', padding: '8px', background: '#f9fafb', borderRadius: 8 }}>
                        <div style={{ fontSize: 20, fontWeight: 700, color: s.color }}>{s.value}</div>
                        <div style={{ fontSize: 11, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{s.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Resolution rate progress bar */}
                  <div>
                    <div className="flex-between" style={{ marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: '#6b7280' }}>Resolution Rate</span>
                      <span style={{ fontSize: 12, fontWeight: 600, color: resolvedPct >= 70 ? '#10b981' : resolvedPct >= 40 ? '#f59e0b' : '#ef4444' }}>
                        {resolvedPct}%
                      </span>
                    </div>
                    <ProgressBar
                      value={intern.resolved}
                      max={total}
                      color={resolvedPct >= 70 ? '#10b981' : resolvedPct >= 40 ? '#f59e0b' : '#ef4444'}
                    />
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Inactive / unapproved Interns */}
      {inactiveInterns.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3>Inactive Interns</h3>
            <span style={{ fontSize: 12, color: '#9ca3af' }}>{inactiveInterns.length} interns</span>
          </div>
          <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr><th>Name</th><th>Username</th><th>Status</th><th>Joined</th><th style={{ textAlign: 'right' }}>Actions</th></tr>
              </thead>
              <tbody>
                {inactiveInterns.map(intern => (
                  <tr key={intern.id}>
                    <td style={{ fontWeight: 600 }}>{intern.full_name}</td>
                    <td style={{ color: '#6b7280', fontSize: 12 }}>@{intern.username}</td>
                    <td>
                      <span className={`badge ${intern.is_active ? 'badge-resolved' : 'badge-closed'}`}>
                        {intern.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td style={{ fontSize: 12, color: '#6b7280' }}>
                      {intern.created_at ? format(new Date(intern.created_at), 'MMM d, yyyy') : '—'}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button className="btn btn-outline btn-sm" onClick={() => toggleStatus(intern)}>
                        {intern.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
