import { useState, useEffect } from 'react'

const INTERVAL_S = 30

export default function RefreshIndicator({ lastUpdated, isRefreshing, onRefresh }) {
  const [tick, setTick] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 1000)
    return () => clearInterval(t)
  }, [])

  const secondsAgo = lastUpdated ? Math.round((Date.now() - lastUpdated.getTime()) / 1000) : null
  const nextIn = secondsAgo !== null ? Math.max(0, INTERVAL_S - secondsAgo) : null

  const label = isRefreshing
    ? 'Refreshing…'
    : secondsAgo === null
      ? 'Loading…'
      : secondsAgo < 5
        ? 'Just updated'
        : `Updated ${secondsAgo}s ago`

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#9ca3af', userSelect: 'none' }}>
      {isRefreshing ? (
        <i className="bi bi-arrow-clockwise" style={{ animation: 'spin 0.8s linear infinite', color: '#3b82f6' }} />
      ) : (
        <span style={{
          display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
          background: secondsAgo !== null ? '#10b981' : '#d1d5db',
        }} />
      )}
      <span>{label}</span>
      {!isRefreshing && nextIn !== null && (
        <span style={{ color: '#d1d5db' }}>· next in {nextIn}s</span>
      )}
      <button
        onClick={onRefresh}
        disabled={isRefreshing}
        title="Refresh now"
        style={{
          background: 'none', border: '1px solid #e5e7eb', cursor: isRefreshing ? 'default' : 'pointer',
          padding: '2px 6px', borderRadius: 5, color: '#9ca3af', fontSize: 12,
          opacity: isRefreshing ? 0.5 : 1, lineHeight: 1,
        }}
      >
        <i className="bi bi-arrow-clockwise" />
      </button>
    </div>
  )
}
