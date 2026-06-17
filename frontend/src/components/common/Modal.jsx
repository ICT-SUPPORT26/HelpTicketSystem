import { useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { StatusBadge, PriorityBadge } from '../StatusBadge'
import { format } from 'date-fns'

const COLOR_MAP = {
  blue:   { bg: '#eff6ff', icon: '#3b82f6', badge: '#dbeafe', text: '#1e40af' },
  yellow: { bg: '#fffbeb', icon: '#f59e0b', badge: '#fde68a', text: '#92400e' },
  cyan:   { bg: '#ecfeff', icon: '#06b6d4', badge: '#cffafe', text: '#164e63' },
  green:  { bg: '#ecfdf5', icon: '#10b981', badge: '#a7f3d0', text: '#065f46' },
  red:    { bg: '#fef2f2', icon: '#ef4444', badge: '#fecaca', text: '#991b1b' },
  gray:   { bg: '#f9fafb', icon: '#6b7280', badge: '#e5e7eb', text: '#374151' },
}

const CARD_META = {
  'Total Tickets':     { description: 'All tickets ever submitted in the system across every status.' },
  'Open':              { description: 'Tickets that have been submitted but not yet picked up by a technician.' },
  'In Progress':       { description: 'Tickets actively being worked on by an assigned technician.' },
  'Resolved':          { description: 'Tickets marked as resolved, pending user confirmation if needed.' },
  'Escalated':         { description: 'High-priority tickets that have been escalated for urgent attention.' },
  'Pending Approvals': { description: 'Intern accounts awaiting administrator approval before they can log in.' },
}

export default function Modal({ isOpen, onClose, card, tickets, loadingTickets }) {
  const navigate = useNavigate()
  const overlayRef = useRef(null)
  const modalRef = useRef(null)
  const closeBtnRef = useRef(null)

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose()
    if (e.key === 'Tab') {
      const focusable = modalRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      if (!focusable?.length) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus() }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus() }
      }
    }
  }, [onClose])

  useEffect(() => {
    if (!isOpen) return
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', handleKeyDown)
    setTimeout(() => closeBtnRef.current?.focus(), 50)
    return () => {
      document.body.style.overflow = ''
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, handleKeyDown])

  if (!isOpen || !card) return null

  const colors = COLOR_MAP[card.color] ?? COLOR_MAP.gray
  const meta = CARD_META[card.label] ?? { description: '' }
  const isPendingApprovals = card.label === 'Pending Approvals'

  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) onClose()
  }

  const handleViewAll = () => {
    onClose()
    navigate(card.link)
  }

  return (
    <div
      ref={overlayRef}
      className="modal-overlay modal-overlay--animated"
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div ref={modalRef} className="modal modal--glass modal--animated" style={{ maxWidth: 560 }}>

        {/* ── Header ── */}
        <div className="modal-header" style={{ borderBottom: `2px solid ${colors.badge}`, background: colors.bg, borderRadius: '20px 20px 0 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 46, height: 46, borderRadius: 12,
              background: colors.badge,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 20, color: colors.icon, flexShrink: 0,
            }}>
              <i className={`bi ${card.icon}`} />
            </div>
            <div>
              <h2 id="modal-title" style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#111827' }}>
                {card.label}
              </h2>
              <p style={{ fontSize: 12, color: '#6b7280', margin: 0 }}>Dashboard overview</p>
            </div>
          </div>
          <button
            ref={closeBtnRef}
            className="btn-icon"
            onClick={onClose}
            aria-label="Close modal"
            style={{ borderRadius: 8, padding: '6px 8px' }}
          >
            <i className="bi bi-x-lg" style={{ fontSize: 16 }} />
          </button>
        </div>

        {/* ── Body ── */}
        <div className="modal-body" style={{ maxHeight: '55vh', overflowY: 'auto', padding: '24px' }}>

          {/* Hero stat */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 20,
            background: colors.bg, borderRadius: 16,
            padding: '20px 24px', marginBottom: 20,
            border: `1px solid ${colors.badge}`,
          }}>
            <div style={{ fontSize: 48, fontWeight: 800, color: colors.icon, lineHeight: 1 }}>
              {card.value}
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>
                {card.label === 'Total Tickets' ? 'Total tickets in system' :
                 card.label === 'Pending Approvals' ? 'Pending intern approvals' :
                 `${card.label} tickets`}
              </div>
              <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4, maxWidth: 280 }}>
                {meta.description}
              </div>
            </div>
          </div>

          {/* Divider */}
          {!isPendingApprovals && (
            <>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <i className="bi bi-clock-history" style={{ color: colors.icon }} />
                Recent Tickets
              </div>

              {loadingTickets ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '32px 0' }}>
                  <span className="spinner" />
                </div>
              ) : tickets?.length ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {tickets.map(t => (
                    <div
                      key={t.id}
                      onClick={() => { onClose(); navigate(`/tickets/${t.id}`) }}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 12,
                        padding: '10px 14px', borderRadius: 10,
                        border: '1px solid #e5e7eb', background: '#fff',
                        cursor: 'pointer', transition: 'all 0.15s',
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = '#f9fafb'}
                      onMouseLeave={e => e.currentTarget.style.background = '#fff'}
                    >
                      <div style={{
                        width: 32, height: 32, borderRadius: 8,
                        background: colors.bg, color: colors.icon,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 13, fontWeight: 700, flexShrink: 0,
                      }}>
                        #{t.id}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 500, fontSize: 13, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {t.location || t.description?.slice(0, 50) || 'Untitled'}
                        </div>
                        <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 1 }}>
                          {t.created_at ? format(new Date(t.created_at), 'MMM d, yyyy') : '—'}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                        <StatusBadge status={t.status} />
                        <PriorityBadge priority={t.priority} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '24px 0', color: '#9ca3af' }}>
                  <i className="bi bi-inbox" style={{ fontSize: 28, display: 'block', marginBottom: 8, opacity: 0.5 }} />
                  <p style={{ fontSize: 13 }}>No tickets found for this category.</p>
                </div>
              )}
            </>
          )}

          {isPendingApprovals && (
            <div className="alert alert-warning" style={{ borderRadius: 12 }}>
              <i className="bi bi-info-circle" style={{ marginRight: 8 }} />
              Visit <strong>User Management</strong> to review and approve pending intern accounts.
            </div>
          )}
        </div>

        {/* ── Footer ── */}
        <div className="modal-footer" style={{ borderTop: '1px solid #e5e7eb', borderRadius: '0 0 20px 20px' }}>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
          <button
            className="btn btn-primary"
            onClick={handleViewAll}
            style={{ background: colors.icon, borderColor: colors.icon }}
          >
            <i className="bi bi-arrow-right-circle" />
            View All
          </button>
        </div>
      </div>
    </div>
  )
}
