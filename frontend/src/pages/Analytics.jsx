import { useState, useEffect } from 'react'
import client from '../api/client'
import LoadingSpinner from '../components/LoadingSpinner'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

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
          <div className="stat-icon" style={{ background: '#eff6ff', color: '#3b82f6' }}><i className="bi bi-ticket-detailed-fill" /></div>
          <div><div className="stat-number">{data.total_tickets}</div><div className="stat-label">Total Tickets</div></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#ecfdf5', color: '#10b981' }}><i className="bi bi-check-circle-fill" /></div>
          <div><div className="stat-number">{data.resolved_tickets}</div><div className="stat-label">Resolved</div></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: slaColor + '18', color: slaColor }}><i className="bi bi-graph-up-arrow" /></div>
          <div>
            <div className="stat-number" style={{ color: slaColor }}>{data.sla_compliance}%</div>
            <div className="stat-label">SLA Compliance</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#ede9fe', color: '#8b5cf6' }}><i className="bi bi-people-fill" /></div>
          <div>
            <div className="stat-number">{data.assignee_workload?.length ?? 0}</div>
            <div className="stat-label">Active Staff</div>
          </div>
        </div>
      </div>

      {/* SLA Gauge */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        <div className="card">
          <div className="card-header"><h3>SLA Compliance</h3></div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 220 }}>
            <div style={{ fontSize: 72, fontWeight: 700, color: slaColor }}>{data.sla_compliance}%</div>
            <div style={{ fontSize: 14, color: '#6b7280', marginTop: 4 }}>
              {data.resolved_tickets} resolved out of {data.total_tickets} total tickets
            </div>
            <div style={{ width: '100%', background: '#f3f4f6', borderRadius: 999, height: 12, marginTop: 20 }}>
              <div style={{ width: `${data.sla_compliance}%`, background: slaColor, height: '100%', borderRadius: 999, transition: 'width 1s ease' }} />
            </div>
          </div>
        </div>

        {/* Status Distribution Pie */}
        <div className="card">
          <div className="card-header"><h3>Status Distribution</h3></div>
          <div className="card-body">
            {statusData.length === 0 ? (
              <div className="empty-state" style={{ padding: 40 }}><i className="bi bi-pie-chart" /><p>No data</p></div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={statusData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                    {statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Assignee Workload */}
      {data.assignee_workload?.length > 0 && (
        <div className="card">
          <div className="card-header"><h3>Staff Workload (Assigned Tickets)</h3></div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.assignee_workload} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 12 }} width={120} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[0,4,4,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}
