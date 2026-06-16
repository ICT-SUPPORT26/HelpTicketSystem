import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import client from '../api/client'
import { StatusBadge, PriorityBadge } from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import { format } from 'date-fns'

const STATUSES = ['', 'open', 'in_progress', 'resolved', 'closed', 'escalated']
const PRIORITIES = ['', 'low', 'medium', 'high', 'urgent']

export default function TicketList() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [tickets, setTickets] = useState([])
  const [meta, setMeta] = useState({ total: 0, pages: 1, current_page: 1 })
  const [loading, setLoading] = useState(true)
  const [categories, setCategories] = useState([])

  const status = searchParams.get('status') || ''
  const priority = searchParams.get('priority') || ''
  const search = searchParams.get('search') || ''
  const category_id = searchParams.get('category_id') || ''
  const page = parseInt(searchParams.get('page') || '1', 10)

  const fetchTickets = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, per_page: 20 }
      if (status) params.status = status
      if (priority) params.priority = priority
      if (search) params.search = search
      if (category_id) params.category_id = category_id
      const res = await client.get('/tickets', { params })
      setTickets(res.data.tickets)
      setMeta({ total: res.data.total, pages: res.data.pages, current_page: res.data.current_page })
    } catch {}
    setLoading(false)
  }, [status, priority, search, category_id, page])

  useEffect(() => {
    fetchTickets()
  }, [fetchTickets])

  useEffect(() => {
    client.get('/categories').then(r => setCategories(r.data)).catch(() => {})
  }, [])

  const setParam = (key, value) => {
    const p = Object.fromEntries(searchParams.entries())
    if (value) p[key] = value; else delete p[key]
    p.page = '1'
    setSearchParams(p)
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Tickets</h1>
          <p className="page-subtitle">{meta.total} ticket{meta.total !== 1 ? 's' : ''} found</p>
        </div>
        <Link to="/tickets/new" className="btn btn-primary">
          <i className="bi bi-plus-circle" /> New Ticket
        </Link>
      </div>

      <div className="card mb-24">
        <div className="card-body" style={{ padding: '12px 16px' }}>
          <div className="filter-bar">
            <input
              className="form-control search-input"
              placeholder="Search tickets…"
              value={search}
              onChange={e => setParam('search', e.target.value)}
            />
            <select className="form-control" value={status} onChange={e => setParam('status', e.target.value)}>
              <option value="">All Statuses</option>
              {STATUSES.filter(Boolean).map(s => (
                <option key={s} value={s}>{s.replace('_', ' ')}</option>
              ))}
            </select>
            <select className="form-control" value={priority} onChange={e => setParam('priority', e.target.value)}>
              <option value="">All Priorities</option>
              {PRIORITIES.filter(Boolean).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <select className="form-control" value={category_id} onChange={e => setParam('category_id', e.target.value)}>
              <option value="">All Categories</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            {(status || priority || search || category_id) && (
              <button className="btn btn-outline btn-sm" onClick={() => setSearchParams({})}>
                <i className="bi bi-x-circle" /> Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner text="Loading tickets…" />
      ) : tickets.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <i className="bi bi-ticket" />
            <p>No tickets found. <Link to="/tickets/new">Create one?</Link></p>
          </div>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th style={{ width: 60 }}>#</th>
                  <th>Location / Description</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Assignees</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map(t => (
                  <tr key={t.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/tickets/${t.id}`)}>
                    <td style={{ color: '#6b7280', fontSize: 12 }}>#{t.id}</td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{t.location}</div>
                      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                        {t.description?.slice(0, 70)}{t.description?.length > 70 ? '…' : ''}
                      </div>
                    </td>
                    <td style={{ fontSize: 12 }}>{t.category?.name || <span style={{ color: '#9ca3af' }}>—</span>}</td>
                    <td><StatusBadge status={t.status} /></td>
                    <td><PriorityBadge priority={t.priority} /></td>
                    <td style={{ fontSize: 12 }}>
                      {t.assignees?.length > 0
                        ? t.assignees.map(a => a.full_name).join(', ')
                        : <span style={{ color: '#9ca3af' }}>Unassigned</span>}
                    </td>
                    <td style={{ fontSize: 12, color: '#6b7280', whiteSpace: 'nowrap' }}>
                      {t.created_at ? format(new Date(t.created_at), 'MMM d, yyyy') : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {meta.pages > 1 && (
            <div className="pagination">
              <button className="page-btn" disabled={page <= 1} onClick={() => setParam('page', String(page - 1))}>
                <i className="bi bi-chevron-left" />
              </button>
              {Array.from({ length: meta.pages }, (_, i) => i + 1).map(p => (
                <button
                  key={p}
                  className={`page-btn ${p === page ? 'active' : ''}`}
                  onClick={() => setParam('page', String(p))}
                >
                  {p}
                </button>
              ))}
              <button className="page-btn" disabled={page >= meta.pages} onClick={() => setParam('page', String(page + 1))}>
                <i className="bi bi-chevron-right" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
