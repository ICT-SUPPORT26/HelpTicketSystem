import { useState, useEffect } from 'react'
import client from '../api/client'
import LoadingSpinner from '../components/LoadingSpinner'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area,
} from 'recharts'
import { format, parseISO } from 'date-fns'

const STATUS_COLORS = ['#f59e0b', '#06b6d4', '#10b981', '#6b7280', '#ef4444']
const CATEGORY_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#f97316', '#ec4899']

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '8px 12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
      <div style={{ fontWeight: 600, marginBottom: 4, color: '#374151' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || '#374151' }}>
          <span style={{ fontWeight: 700 }}>{p.value}</span>
          {p.name === 'count' ? ' tickets' : ''}
        </div>
      ))}
    </div>
  )
}

const DonutCenter = ({ viewBox, total, resolved }) => {
  const { cx, cy } = viewBox
  const pct = total > 0 ? Math.round((resolved / total) * 100) : 0
  return (
    <>
      <text x={cx} y={cy - 8} textAnchor="middle" style={{ fontSize: 22, fontWeight: 700, fill: '#111827' }}>{pct}%</text>
      <text x={cx} y={cy + 12} textAnchor="middle" style={{ fontSize: 11, fill: '#6b7280' }}>resolved</text>
    </>
  )
}

function SlaRing({ value }) {
  const color = value >= 80 ? '#10b981' : value >= 50 ? '#f59e0b' : '#ef4444'
  const r = 54, cx = 70, cy = 70
  const circ = 2 * Math.PI * r
  const dash = (value / 100) * circ
  return (
    <svg width={140} height={140} style={{ display: 'block', margin: '0 auto' }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#f3f4f6" strokeWidth={10} />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={10}
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}
        style={{ transition: 'stroke-dasharray 1s ease' }} />
      <text x={cx} y={cy - 6} textAnchor="middle" style={{ fontSize: 22, fontWeight: 700, fill: color }}>{value}%</text>
      <text x={cx} y={cy + 14} textAnchor="middle" style={{ fontSize: 11, fill: '#6b7280' }}>SLA</text>
    </svg>
  )
}

function WorkloadRow({ name, count, max }) {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0
  const initials = name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
  const hue = (name.charCodeAt(0) * 37) % 360
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
      <div style={{
        width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
        background: `hsl(${hue}, 60%, 90%)`, color: `hsl(${hue}, 60%, 35%)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 11, fontWeight: 700,
      }}>{initials}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 140 }}>{name}</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: '#3b82f6', flexShrink: 0 }}>{count}</span>
        </div>
        <div style={{ background: '#f3f4f6', borderRadius: 999, height: 6 }}>
          <div style={{ width: `${pct}%`, background: `hsl(${hue}, 60%, 55%)`, height: '100%', borderRadius: 999, transition: 'width 0.8s ease' }} />
        </div>
      </div>
    </div>
  )
}

export default function Analytics() {
  const [data, setData] = useState(null)
  const [reportStats, setReportStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      client.get('/analytics/stats'),
      client.get('/reports/stats'),
    ]).then(([analRes, repRes]) => {
      setData(analRes.data)
      setReportStats(repRes.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner size="lg" text="Loading analytics…" />
  if (!data) return null

  const slaColor = data.sla_compliance >= 80 ? '#10b981' : data.sla_compliance >= 50 ? '#f59e0b' : '#ef4444'

  const statusData = reportStats ? [
    { name: 'Open', value: reportStats.open },
    { name: 'In Progress', value: reportStats.in_progress },
    { name: 'Resolved', value: reportStats.resolved },
    { name: 'Closed', value: reportStats.closed },
    { name: 'Escalated', value: reportStats.escalated },
  ].filter(d => d.value > 0) : []

  const topCategories = reportStats?.by_category
    ? [...reportStats.by_category].sort((a, b) => b.count - a.count).slice(0, 8)
    : []

  const daily = reportStats?.daily_volume?.slice(-30) || []

  const maxWorkload = data.assignee_workload?.length
    ? Math.max(...data.assignee_workload.map(w => w.count))
    : 1

  const totalOpen = (reportStats?.open || 0) + (reportStats?.in_progress || 0) + (reportStats?.escalated || 0)
  const pendingPct = data.total_tickets > 0
    ? Math.round((totalOpen / data.total_tickets) * 100)
    : 0

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">System performance insights</p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="stats-grid mb-24">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#eff6ff', color: '#3b82f6' }}>
            <i className="bi bi-ticket-detailed-fill" />
          </div>
          <div>
            <div className="stat-number">{data.total_tickets}</div>
            <div className="stat-label">Total Tickets</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#ecfdf5', color: '#10b981' }}>
            <i className="bi bi-check-circle-fill" />
          </div>
          <div>
            <div className="stat-number">{data.resolved_tickets}</div>
            <div className="stat-label">Resolved</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: slaColor + '18', color: slaColor }}>
            <i className="bi bi-graph-up-arrow" />
          </div>
          <div>
            <div className="stat-number" style={{ color: slaColor }}>{data.sla_compliance}%</div>
            <div className="stat-label">SLA Compliance</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#fef3c7', color: '#f59e0b' }}>
            <i className="bi bi-hourglass-split" />
          </div>
          <div>
            <div className="stat-number" style={{ color: '#f59e0b' }}>{totalOpen}</div>
            <div className="stat-label">Pending ({pendingPct}%)</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#ede9fe', color: '#8b5cf6' }}>
            <i className="bi bi-people-fill" />
          </div>
          <div>
            <div className="stat-number">{data.assignee_workload?.length ?? 0}</div>
            <div className="stat-label">Active Staff</div>
          </div>
        </div>
      </div>

      {/* Row 1: SLA Ring + Status Donut + Volume Trend */}
      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* SLA Ring */}
        <div className="card">
          <div className="card-header"><h3 style={{ margin: 0 }}>SLA</h3></div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <SlaRing value={data.sla_compliance} />
            <div style={{ fontSize: 12, color: '#6b7280', textAlign: 'center', marginTop: 8 }}>
              {data.resolved_tickets} of {data.total_tickets} resolved
            </div>
          </div>
        </div>

        {/* Status Donut */}
        <div className="card">
          <div className="card-header"><h3 style={{ margin: 0 }}>Status Distribution</h3></div>
          <div className="card-body">
            {statusData.length === 0 ? (
              <div className="empty-state" style={{ padding: 40 }}><i className="bi bi-pie-chart" /><p>No data</p></div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie data={statusData} cx="50%" cy="50%" innerRadius={52} outerRadius={76}
                      dataKey="value" paddingAngle={2} startAngle={90} endAngle={-270}>
                      {statusData.map((_, i) => <Cell key={i} fill={STATUS_COLORS[i % STATUS_COLORS.length]} />)}
                      <DonutCenter viewBox={{ cx: 0, cy: 0 }}
                        total={data.total_tickets} resolved={data.resolved_tickets} />
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 12px', justifyContent: 'center' }}>
                  {statusData.map((s, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#6b7280' }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: STATUS_COLORS[i] }} />
                      {s.name}: <strong style={{ color: '#374151' }}>{s.value}</strong>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>

        {/* 30-Day Trend */}
        <div className="card">
          <div className="card-header">
            <h3 style={{ margin: 0 }}>30-Day Ticket Trend</h3>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={daily} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
                <defs>
                  <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#9ca3af' }}
                  tickFormatter={d => { try { return format(parseISO(d), 'MM/dd') } catch { return d.slice(5) } }}
                  interval={6} />
                <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={2}
                  fill="url(#trendGrad)" dot={false}
                  activeDot={{ r: 4, fill: '#8b5cf6', stroke: '#fff', strokeWidth: 2 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Row 2: Top Categories + Staff Workload */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Top Categories */}
        <div className="card">
          <div className="card-header"><h3 style={{ margin: 0 }}>Top Categories</h3></div>
          <div className="card-body">
            {topCategories.length === 0 ? (
              <div className="empty-state" style={{ padding: 40 }}><i className="bi bi-tags" /><p>No category data</p></div>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={topCategories} layout="vertical" margin={{ top: 0, right: 40, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11, fill: '#9ca3af' }} allowDecimals={false} />
                  <YAxis dataKey="category" type="category" tick={{ fontSize: 11, fill: '#374151' }} width={120} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}
                    label={{ position: 'right', fontSize: 11, fill: '#6b7280' }}>
                    {topCategories.map((_, i) => (
                      <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Staff Workload */}
        <div className="card">
          <div className="card-header">
            <h3 style={{ margin: 0 }}>Staff Workload</h3>
            <p style={{ fontSize: 12, color: '#6b7280', margin: 0 }}>Active ticket assignments</p>
          </div>
          <div className="card-body">
            {!data.assignee_workload?.length ? (
              <div className="empty-state" style={{ padding: 40 }}>
                <i className="bi bi-people" /><p>No assignments yet</p>
              </div>
            ) : (
              <div style={{ paddingTop: 4 }}>
                {data.assignee_workload.map((w, i) => (
                  <WorkloadRow key={i} name={w.name} count={w.count} max={maxWorkload} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Priority breakdown across all tickets */}
      {reportStats?.by_priority && (
        <div className="card">
          <div className="card-header"><h3 style={{ margin: 0 }}>Priority Distribution</h3></div>
          <div className="card-body" style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            {reportStats.by_priority.map((p, i) => {
              const colors = { low: '#10b981', medium: '#f59e0b', high: '#f97316', urgent: '#ef4444' }
              const c = colors[p.priority] || '#3b82f6'
              const pct = data.total_tickets > 0 ? Math.round((p.count / data.total_tickets) * 100) : 0
              return (
                <div key={i} style={{
                  flex: 1, minWidth: 120, background: c + '10', border: `1px solid ${c}30`,
                  borderRadius: 10, padding: '14px 16px', textAlign: 'center',
                }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: c }}>{p.count}</div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: c, textTransform: 'capitalize', marginBottom: 6 }}>{p.priority}</div>
                  <div style={{ background: c + '25', borderRadius: 999, height: 4 }}>
                    <div style={{ width: `${pct}%`, background: c, height: '100%', borderRadius: 999 }} />
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>{pct}% of total</div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
