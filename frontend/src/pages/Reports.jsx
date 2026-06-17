import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'
import LoadingSpinner from '../components/LoadingSpinner'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, ReferenceLine, Legend,
} from 'recharts'
import { format, subDays, parseISO } from 'date-fns'

const PRIORITY_COLORS = { low: '#10b981', medium: '#f59e0b', high: '#f97316', urgent: '#ef4444' }
const STATUS_COLORS = {
  total: '#3b82f6', open: '#f59e0b', in_progress: '#06b6d4',
  resolved: '#10b981', closed: '#6b7280', escalated: '#ef4444',
}

const QUICK_PERIODS = [
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
  { label: 'All', days: null },
]

const CustomAreaTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '8px 12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
      <div style={{ fontWeight: 600, marginBottom: 4, color: '#374151' }}>{label}</div>
      <div style={{ color: '#3b82f6', fontWeight: 700 }}>{payload[0].value} ticket{payload[0].value !== 1 ? 's' : ''}</div>
    </div>
  )
}

const CustomBarTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '8px 12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
      <div style={{ fontWeight: 600, marginBottom: 4, color: '#374151', textTransform: 'capitalize' }}>{label}</div>
      <div style={{ color: '#374151' }}><span style={{ fontWeight: 700 }}>{payload[0].value}</span> tickets</div>
    </div>
  )
}

function TrendBadge({ current, previous }) {
  if (previous === 0 && current === 0) return null
  if (previous === 0) return <span style={{ fontSize: 11, color: '#10b981', fontWeight: 600 }}>New ↑</span>
  const pct = Math.round(((current - previous) / previous) * 100)
  const up = pct >= 0
  return (
    <span style={{ fontSize: 11, fontWeight: 600, color: up ? '#ef4444' : '#10b981' }}>
      {up ? '↑' : '↓'} {Math.abs(pct)}%
    </span>
  )
}

export default function Reports() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [dateRange, setDateRange] = useState({ start: '', end: '' })
  const [activePeriod, setActivePeriod] = useState('30d')

  const fetchStats = useCallback(async (dates = dateRange) => {
    setLoading(true)
    try {
      const params = {}
      if (dates.start) params.start = dates.start
      if (dates.end) params.end = dates.end
      const res = await client.get('/reports/stats', { params })
      setStats(res.data)
    } catch {}
    setLoading(false)
  }, [dateRange])

  useEffect(() => { fetchStats() }, [])

  const applyQuickPeriod = (p) => {
    setActivePeriod(p.label)
    if (!p.days) {
      const empty = { start: '', end: '' }
      setDateRange(empty)
      fetchStats(empty)
    } else {
      const start = format(subDays(new Date(), p.days), 'yyyy-MM-dd')
      const end = format(new Date(), 'yyyy-MM-dd')
      const range = { start, end }
      setDateRange(range)
      fetchStats(range)
    }
  }

  const statCards = stats ? [
    { label: 'Total', value: stats.total, color: STATUS_COLORS.total, icon: 'bi-ticket-detailed-fill' },
    { label: 'Open', value: stats.open, color: STATUS_COLORS.open, icon: 'bi-folder2-open' },
    { label: 'In Progress', value: stats.in_progress, color: STATUS_COLORS.in_progress, icon: 'bi-arrow-clockwise' },
    { label: 'Resolved', value: stats.resolved, color: STATUS_COLORS.resolved, icon: 'bi-check-circle-fill' },
    { label: 'Closed', value: stats.closed, color: STATUS_COLORS.closed, icon: 'bi-archive-fill' },
    { label: 'Escalated', value: stats.escalated, color: STATUS_COLORS.escalated, icon: 'bi-exclamation-triangle-fill' },
  ] : []

  const resolutionRate = stats && stats.total > 0
    ? Math.round(((stats.resolved + stats.closed) / stats.total) * 100)
    : 0

  const filteredVolume = stats?.daily_volume
    ? (activePeriod === '7d'
        ? stats.daily_volume.slice(-7)
        : activePeriod === '90d'
          ? stats.daily_volume
          : stats.daily_volume.slice(-30))
    : []

  const avgDaily = filteredVolume.length
    ? (filteredVolume.reduce((s, d) => s + d.count, 0) / filteredVolume.length).toFixed(1)
    : 0

  const firstHalf = filteredVolume.slice(0, Math.floor(filteredVolume.length / 2))
  const secondHalf = filteredVolume.slice(Math.floor(filteredVolume.length / 2))
  const firstSum = firstHalf.reduce((s, d) => s + d.count, 0)
  const secondSum = secondHalf.reduce((s, d) => s + d.count, 0)

  const priorityData = stats?.by_priority?.map(p => ({
    ...p,
    fill: PRIORITY_COLORS[p.priority] || '#3b82f6',
  })) || []

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">Ticket statistics and trends</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-24">
        <div className="card-body" style={{ padding: '12px 16px' }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: 6 }}>
              {QUICK_PERIODS.map(p => (
                <button key={p.label}
                  onClick={() => applyQuickPeriod(p)}
                  style={{
                    padding: '4px 12px', borderRadius: 6, border: '1px solid',
                    borderColor: activePeriod === p.label ? '#3b82f6' : '#e5e7eb',
                    background: activePeriod === p.label ? '#3b82f6' : '#fff',
                    color: activePeriod === p.label ? '#fff' : '#374151',
                    fontWeight: 500, fontSize: 13, cursor: 'pointer',
                  }}>
                  {p.label}
                </button>
              ))}
            </div>
            <div style={{ width: 1, height: 28, background: '#e5e7eb' }} />
            <div className="flex gap-8">
              <label className="form-label" style={{ marginBottom: 0, whiteSpace: 'nowrap', alignSelf: 'center', fontSize: 13 }}>From</label>
              <input type="date" className="form-control" style={{ fontSize: 13, padding: '4px 8px' }}
                value={dateRange.start}
                onChange={e => { setDateRange(d => ({ ...d, start: e.target.value })); setActivePeriod('') }} />
            </div>
            <div className="flex gap-8">
              <label className="form-label" style={{ marginBottom: 0, whiteSpace: 'nowrap', alignSelf: 'center', fontSize: 13 }}>To</label>
              <input type="date" className="form-control" style={{ fontSize: 13, padding: '4px 8px' }}
                value={dateRange.end}
                onChange={e => { setDateRange(d => ({ ...d, end: e.target.value })); setActivePeriod('') }} />
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => fetchStats()}>
              <i className="bi bi-search" /> Apply
            </button>
            <button className="btn btn-outline btn-sm" onClick={() => {
              const empty = { start: '', end: '' }
              setDateRange(empty)
              setActivePeriod('30d')
              fetchStats(empty)
            }}>Reset</button>
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
                  <i className={`bi ${c.icon}`} />
                </div>
                <div>
                  <div className="stat-number" style={{ color: c.color }}>{c.value}</div>
                  <div className="stat-label">{c.label}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Resolution Rate Banner */}
          <div className="card mb-20" style={{ background: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)', border: 'none' }}>
            <div className="card-body" style={{ padding: '16px 20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <div>
                  <div style={{ color: '#bfdbfe', fontSize: 12, fontWeight: 500, marginBottom: 2 }}>RESOLUTION RATE</div>
                  <div style={{ color: '#fff', fontSize: 28, fontWeight: 700 }}>{resolutionRate}%</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#bfdbfe', fontSize: 12 }}>{stats.resolved + stats.closed} resolved + closed</div>
                  <div style={{ color: '#bfdbfe', fontSize: 12 }}>out of {stats.total} total</div>
                </div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.2)', borderRadius: 999, height: 8 }}>
                <div style={{ width: `${resolutionRate}%`, background: '#fff', height: '100%', borderRadius: 999, transition: 'width 1s ease' }} />
              </div>
            </div>
          </div>

          {/* Daily Volume */}
          <div className="card mb-20">
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0 }}>Ticket Volume Over Time</h3>
                <p style={{ fontSize: 12, color: '#6b7280', margin: 0 }}>Daily submissions for selected period</p>
              </div>
              <div style={{ display: 'flex', gap: 20, fontSize: 13 }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#6b7280' }}>Avg/day</div>
                  <div style={{ fontWeight: 700, color: '#3b82f6' }}>{avgDaily}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#6b7280' }}>Trend</div>
                  <TrendBadge current={secondSum} previous={firstSum} />
                </div>
              </div>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={filteredVolume} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
                  <defs>
                    <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickFormatter={d => {
                      try { return format(parseISO(d), filteredVolume.length <= 14 ? 'MMM d' : 'MM/dd') }
                      catch { return d.slice(5) }
                    }}
                    interval={filteredVolume.length <= 14 ? 0 : 'preserveStartEnd'}
                  />
                  <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} allowDecimals={false} />
                  <Tooltip content={<CustomAreaTooltip />} />
                  {avgDaily > 0 && (
                    <ReferenceLine y={parseFloat(avgDaily)} stroke="#f59e0b" strokeDasharray="4 4"
                      label={{ value: 'avg', position: 'right', fontSize: 10, fill: '#f59e0b' }} />
                  )}
                  <Area type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2.5}
                    fill="url(#volumeGradient)" dot={filteredVolume.length <= 14}
                    activeDot={{ r: 5, fill: '#3b82f6', stroke: '#fff', strokeWidth: 2 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* By Category + By Priority */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
            {/* By Category */}
            <div className="card">
              <div className="card-header"><h3 style={{ margin: 0 }}>Tickets by Category</h3></div>
              <div className="card-body">
                {!stats.by_category?.length ? (
                  <div className="empty-state" style={{ padding: 40 }}>
                    <i className="bi bi-bar-chart" /><p>No data</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={stats.by_category} margin={{ top: 5, right: 5, bottom: 30, left: -20 }}>
                      <defs>
                        <linearGradient id="catGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3b82f6" />
                          <stop offset="100%" stopColor="#6366f1" />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
                      <XAxis dataKey="category" tick={{ fontSize: 10, fill: '#9ca3af' }} angle={-35} textAnchor="end" interval={0} />
                      <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} allowDecimals={false} />
                      <Tooltip content={<CustomBarTooltip />} />
                      <Bar dataKey="count" fill="url(#catGradient)" radius={[4, 4, 0, 0]}
                        label={{ position: 'top', fontSize: 10, fill: '#6b7280' }} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* By Priority */}
            <div className="card">
              <div className="card-header"><h3 style={{ margin: 0 }}>Tickets by Priority</h3></div>
              <div className="card-body">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={priorityData} margin={{ top: 5, right: 5, bottom: 10, left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
                    <XAxis dataKey="priority" tick={{ fontSize: 12, fill: '#9ca3af', textTransform: 'capitalize' }}
                      tickFormatter={v => v.charAt(0).toUpperCase() + v.slice(1)} />
                    <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} allowDecimals={false} />
                    <Tooltip content={<CustomBarTooltip />} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}
                      label={{ position: 'top', fontSize: 10, fill: '#6b7280' }}>
                      {priorityData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 8 }}>
                  {Object.entries(PRIORITY_COLORS).map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#6b7280' }}>
                      <div style={{ width: 10, height: 10, borderRadius: 2, background: v }} />
                      <span style={{ textTransform: 'capitalize' }}>{k}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Category Table */}
          {stats.by_category?.length > 0 && (
            <div className="card">
              <div className="card-header"><h3 style={{ margin: 0 }}>Category Breakdown</h3></div>
              <div className="card-body" style={{ padding: 0 }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <th style={{ padding: '10px 16px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>Category</th>
                      <th style={{ padding: '10px 16px', textAlign: 'right', color: '#6b7280', fontWeight: 600 }}>Tickets</th>
                      <th style={{ padding: '10px 16px', textAlign: 'right', color: '#6b7280', fontWeight: 600 }}>% of Total</th>
                      <th style={{ padding: '10px 16px', width: 180 }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...stats.by_category].sort((a, b) => b.count - a.count).map((c, i) => {
                      const pct = stats.total > 0 ? Math.round((c.count / stats.total) * 100) : 0
                      return (
                        <tr key={i} style={{ borderBottom: '1px solid #f9fafb' }}>
                          <td style={{ padding: '10px 16px', fontWeight: 500 }}>{c.category}</td>
                          <td style={{ padding: '10px 16px', textAlign: 'right', fontWeight: 700, color: '#3b82f6' }}>{c.count}</td>
                          <td style={{ padding: '10px 16px', textAlign: 'right', color: '#6b7280' }}>{pct}%</td>
                          <td style={{ padding: '10px 16px' }}>
                            <div style={{ background: '#f3f4f6', borderRadius: 999, height: 6 }}>
                              <div style={{ width: `${pct}%`, background: '#3b82f6', height: '100%', borderRadius: 999 }} />
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
