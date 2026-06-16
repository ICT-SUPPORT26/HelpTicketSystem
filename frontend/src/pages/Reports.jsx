import { useState, useEffect } from 'react'
import client from '../api/client'
import LoadingSpinner from '../components/LoadingSpinner'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

export default function Reports() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [dateRange, setDateRange] = useState({ start: '', end: '' })

  const fetchStats = async (dates = dateRange) => {
    setLoading(true)
    try {
      const params = {}
      if (dates.start) params.start = dates.start
      if (dates.end) params.end = dates.end
      const res = await client.get('/reports/stats', { params })
      setStats(res.data)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { fetchStats() }, [])

  const statCards = stats ? [
    { label: 'Total', value: stats.total, color: '#3b82f6' },
    { label: 'Open', value: stats.open, color: '#f59e0b' },
    { label: 'In Progress', value: stats.in_progress, color: '#06b6d4' },
    { label: 'Resolved', value: stats.resolved, color: '#10b981' },
    { label: 'Closed', value: stats.closed, color: '#6b7280' },
    { label: 'Escalated', value: stats.escalated, color: '#ef4444' },
  ] : []

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">Ticket statistics and trends</p>
        </div>
      </div>

      {/* Date Filter */}
      <div className="card mb-24">
        <div className="card-body" style={{ padding: '12px 16px' }}>
          <div className="filter-bar">
            <div className="flex gap-8">
              <label className="form-label" style={{ marginBottom: 0, whiteSpace: 'nowrap', alignSelf: 'center' }}>From</label>
              <input type="date" className="form-control" value={dateRange.start} onChange={e => setDateRange(d => ({ ...d, start: e.target.value }))} />
            </div>
            <div className="flex gap-8">
              <label className="form-label" style={{ marginBottom: 0, whiteSpace: 'nowrap', alignSelf: 'center' }}>To</label>
              <input type="date" className="form-control" value={dateRange.end} onChange={e => setDateRange(d => ({ ...d, end: e.target.value }))} />
            </div>
            <button className="btn btn-primary btn-sm" onClick={fetchStats}>
              <i className="bi bi-search" /> Apply
            </button>
            <button className="btn btn-outline btn-sm" onClick={() => {
              const empty = { start: '', end: '' }
              setDateRange(empty)
              fetchStats(empty)
            }}>
              Reset
            </button>
          </div>
        </div>
      </div>

      {loading ? <LoadingSpinner size="lg" text="Loading reports…" /> : !stats ? null : (
        <>
          {/* Stat Cards */}
          <div className="stats-grid mb-24">
            {statCards.map(c => (
              <div key={c.label} className="stat-card">
                <div className="stat-icon" style={{ background: c.color + '18', color: c.color }}>
                  <i className="bi bi-ticket-detailed" />
                </div>
                <div><div className="stat-number">{c.value}</div><div className="stat-label">{c.label}</div></div>
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
            {/* By Category */}
            <div className="card">
              <div className="card-header"><h3>Tickets by Category</h3></div>
              <div className="card-body">
                {stats.by_category?.length === 0 ? (
                  <div className="empty-state" style={{ padding: 40 }}><i className="bi bi-bar-chart" /><p>No data</p></div>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={stats.by_category} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                      <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#3b82f6" radius={[4,4,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* By Priority */}
            <div className="card">
              <div className="card-header"><h3>Tickets by Priority</h3></div>
              <div className="card-body">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={stats.by_priority} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="priority" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#10b981" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Daily Volume */}
          <div className="card">
            <div className="card-header"><h3>Daily Ticket Volume (Last 30 Days)</h3></div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={stats.daily_volume} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
