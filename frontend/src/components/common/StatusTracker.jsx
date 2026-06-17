import { format, formatDistanceToNow } from 'date-fns'

/* ── Status pipeline definition ─────────────────────────── */
const PIPELINE = [
  { key: 'open',        label: 'Open',        icon: 'bi-folder2-open',          color: '#f59e0b', bg: '#fffbeb' },
  { key: 'in_progress', label: 'In Progress', icon: 'bi-arrow-repeat',           color: '#06b6d4', bg: '#ecfeff' },
  { key: 'resolved',    label: 'Resolved',    icon: 'bi-check-circle-fill',      color: '#10b981', bg: '#ecfdf5' },
  { key: 'closed',      label: 'Closed',      icon: 'bi-lock-fill',              color: '#6b7280', bg: '#f9fafb' },
]

const ESCALATED_STEP = {
  key: 'escalated', label: 'Escalated', icon: 'bi-exclamation-triangle-fill', color: '#ef4444', bg: '#fef2f2',
}

/* ── Action → visual mapping ─────────────────────────────── */
const ACTION_META = {
  'created':          { icon: 'bi-plus-circle-fill',       color: '#3b82f6', bg: '#eff6ff',  label: 'Ticket created'          },
  'status changed':   { icon: 'bi-arrow-left-right',       color: '#8b5cf6', bg: '#f5f3ff',  label: 'Status changed'          },
  'priority changed': { icon: 'bi-flag-fill',              color: '#f59e0b', bg: '#fffbeb',  label: 'Priority changed'        },
  'escalated':        { icon: 'bi-exclamation-triangle-fill', color: '#ef4444', bg: '#fef2f2', label: 'Escalated'             },
  'closed':           { icon: 'bi-lock-fill',              color: '#6b7280', bg: '#f9fafb',  label: 'Closed'                  },
  'assignees updated':{ icon: 'bi-people-fill',            color: '#10b981', bg: '#ecfdf5',  label: 'Assignees updated'       },
  'comment added':    { icon: 'bi-chat-fill',              color: '#06b6d4', bg: '#ecfeff',  label: 'Comment added'           },
}
const DEFAULT_META = { icon: 'bi-circle-fill', color: '#9ca3af', bg: '#f3f4f6', label: 'Activity' }

const STATUS_COLOR = {
  open:        { color: '#f59e0b', bg: '#fffbeb' },
  in_progress: { color: '#06b6d4', bg: '#ecfeff' },
  resolved:    { color: '#10b981', bg: '#ecfdf5' },
  closed:      { color: '#6b7280', bg: '#f9fafb' },
  escalated:   { color: '#ef4444', bg: '#fef2f2' },
}

/* ── Horizontal stepper ──────────────────────────────────── */
function StatusStepper({ currentStatus, history }) {
  const isEscalated = currentStatus === 'escalated'
  const steps = isEscalated
    ? [PIPELINE[0], PIPELINE[1], ESCALATED_STEP]
    : PIPELINE

  const currentIdx = steps.findIndex(s => s.key === currentStatus)

  return (
    <div style={{ padding: '20px 24px 16px' }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 18 }}>
        Ticket Progress
      </div>
      <div style={{ display: 'flex', alignItems: 'center', position: 'relative' }}>
        {steps.map((step, i) => {
          const isDone    = i < currentIdx
          const isCurrent = i === currentIdx
          const isPending = i > currentIdx

          /* find timestamp for this status from history */
          const histEntry = history?.find(h =>
            (h.action === 'created' && step.key === 'open') ||
            (h.action === 'status changed' && h.new_value === step.key) ||
            (h.action === step.key)
          )

          return (
            <div key={step.key} style={{ display: 'flex', alignItems: 'center', flex: i < steps.length - 1 ? 1 : 'none' }}>
              {/* Step bubble */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 1 }}>
                <div
                  style={{
                    width: 40, height: 40, borderRadius: '50%',
                    background: isPending ? '#f3f4f6' : step.bg,
                    border: isCurrent
                      ? `3px solid ${step.color}`
                      : isPending
                        ? '2px solid #e5e7eb'
                        : `2px solid ${step.color}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    boxShadow: isCurrent ? `0 0 0 4px ${step.color}22` : 'none',
                    transition: 'all 0.3s ease',
                    position: 'relative',
                  }}
                >
                  {isDone ? (
                    <i className="bi bi-check-lg" style={{ color: step.color, fontSize: 16, fontWeight: 700 }} />
                  ) : (
                    <i
                      className={`bi ${step.icon}`}
                      style={{ color: isPending ? '#d1d5db' : step.color, fontSize: 15 }}
                    />
                  )}
                  {isCurrent && (
                    <span style={{
                      position: 'absolute', inset: -4, borderRadius: '50%',
                      border: `2px solid ${step.color}`,
                      animation: 'stepPulse 2s ease-out infinite',
                      pointerEvents: 'none',
                    }} />
                  )}
                </div>
                <div style={{ marginTop: 8, textAlign: 'center' }}>
                  <div style={{
                    fontSize: 11, fontWeight: isCurrent ? 700 : 500,
                    color: isPending ? '#d1d5db' : isCurrent ? step.color : '#374151',
                    whiteSpace: 'nowrap',
                  }}>
                    {step.label}
                  </div>
                  {histEntry?.timestamp && (
                    <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 2, whiteSpace: 'nowrap' }}>
                      {format(new Date(histEntry.timestamp), 'MMM d, HH:mm')}
                    </div>
                  )}
                </div>
              </div>

              {/* Connector line */}
              {i < steps.length - 1 && (
                <div style={{
                  flex: 1, height: 3, marginBottom: 28, marginLeft: 4, marginRight: 4,
                  background: i < currentIdx
                    ? `linear-gradient(90deg, ${steps[i].color}, ${steps[i + 1].color})`
                    : '#e5e7eb',
                  borderRadius: 2, transition: 'background 0.4s ease',
                }} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ── Timeline entry ──────────────────────────────────────── */
function TimelineEntry({ entry, isLast }) {
  const meta = ACTION_META[entry.action] ?? DEFAULT_META
  const hasChange = entry.old_value && entry.new_value
  const oldC = STATUS_COLOR[entry.old_value]
  const newC = STATUS_COLOR[entry.new_value]

  return (
    <div style={{ display: 'flex', gap: 14, paddingBottom: isLast ? 0 : 20, position: 'relative' }}>
      {/* Vertical track */}
      {!isLast && (
        <div style={{
          position: 'absolute', left: 17, top: 36, bottom: 0, width: 2,
          background: 'linear-gradient(180deg, #e5e7eb 0%, transparent 100%)',
        }} />
      )}

      {/* Icon bubble */}
      <div style={{ flexShrink: 0, zIndex: 1 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: meta.bg, border: `2px solid ${meta.color}22`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <i className={`bi ${meta.icon}`} style={{ color: meta.color, fontSize: 14 }} />
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, paddingTop: 6 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', flexWrap: 'wrap', gap: 6, marginBottom: 4 }}>
          <span style={{ fontWeight: 600, fontSize: 13, color: '#111827' }}>
            {entry.action.charAt(0).toUpperCase() + entry.action.slice(1)}
          </span>
          {entry.field_changed && (
            <span style={{ fontSize: 11, color: '#6b7280' }}>· {entry.field_changed}</span>
          )}
        </div>

        {/* Old → New value pill */}
        {hasChange && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, flexWrap: 'wrap' }}>
            <span style={{
              padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
              background: oldC?.bg ?? '#f3f4f6', color: oldC?.color ?? '#6b7280',
            }}>
              {entry.old_value.replace('_', ' ')}
            </span>
            <i className="bi bi-arrow-right" style={{ color: '#9ca3af', fontSize: 11 }} />
            <span style={{
              padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
              background: newC?.bg ?? '#f3f4f6', color: newC?.color ?? '#374151',
            }}>
              {entry.new_value.replace('_', ' ')}
            </span>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {entry.user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <div style={{
                width: 18, height: 18, borderRadius: '50%', background: '#3b82f6',
                color: 'white', fontSize: 9, fontWeight: 700,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                {entry.user.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
              </div>
              <span style={{ fontSize: 12, color: '#6b7280' }}>{entry.user.full_name}</span>
            </div>
          )}
          {entry.user && entry.timestamp && (
            <span style={{ color: '#d1d5db', fontSize: 10 }}>·</span>
          )}
          {entry.timestamp && (
            <span
              title={format(new Date(entry.timestamp), 'MMM d, yyyy HH:mm:ss')}
              style={{ fontSize: 11, color: '#9ca3af', cursor: 'default' }}
            >
              {formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

/* ── Main exported component ─────────────────────────────── */
export default function StatusTracker({ ticket }) {
  const history = ticket?.history ?? []

  return (
    <div className="card" style={{ marginBottom: 16, overflow: 'hidden' }}>
      {/* Stepper */}
      <div style={{ borderBottom: '1px solid #f3f4f6', background: '#fafafa' }}>
        <StatusStepper currentStatus={ticket?.status} history={history} />
      </div>

      {/* Timeline */}
      <div className="card-header" style={{ paddingBottom: 12 }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <i className="bi bi-activity" style={{ color: '#3b82f6' }} />
          Activity Timeline
        </h3>
        <span style={{ fontSize: 12, color: '#9ca3af', fontWeight: 400 }}>
          {history.length} event{history.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="card-body" style={{ paddingTop: 16 }}>
        {history.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px 0', color: '#9ca3af' }}>
            <i className="bi bi-clock-history" style={{ fontSize: 28, display: 'block', marginBottom: 8, opacity: 0.4 }} />
            <span style={{ fontSize: 13 }}>No activity recorded yet.</span>
          </div>
        ) : (
          [...history].reverse().map((h, i) => (
            <TimelineEntry key={h.id} entry={h} isLast={i === history.length - 1} />
          ))
        )}
      </div>
    </div>
  )
}
