export default function DashboardCard({ card, onClick }) {
  return (
    <div
      className="stat-card stat-card--clickable"
      onClick={() => onClick(card)}
      role="button"
      tabIndex={0}
      aria-label={`${card.label}: ${card.value}. Click to view details.`}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick(card)}
    >
      <div className={`stat-icon ${card.color}`}>
        <i className={`bi ${card.icon}`} />
      </div>
      <div>
        <div className="stat-number">{card.value}</div>
        <div className="stat-label">{card.label}</div>
      </div>
      <div className="stat-card__chevron">
        <i className="bi bi-chevron-right" />
      </div>
    </div>
  )
}
