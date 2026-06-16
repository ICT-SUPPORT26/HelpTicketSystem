export function StatusBadge({ status }) {
  const labels = {
    open: 'Open',
    in_progress: 'In Progress',
    resolved: 'Resolved',
    closed: 'Closed',
    escalated: 'Escalated',
  }
  return (
    <span className={`badge badge-${status}`}>
      {labels[status] || status}
    </span>
  )
}

export function PriorityBadge({ priority }) {
  const icons = { low: '▼', medium: '●', high: '▲', urgent: '⚠' }
  return (
    <span className={`badge badge-${priority}`}>
      {icons[priority]} {priority}
    </span>
  )
}

export function RoleBadge({ role }) {
  return <span className={`badge badge-${role}`}>{role}</span>
}
