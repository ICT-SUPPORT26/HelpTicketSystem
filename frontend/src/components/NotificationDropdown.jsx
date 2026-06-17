import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'
import { formatDistanceToNow } from 'date-fns'

export default function NotificationDropdown() {
  const [open, setOpen] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [unread, setUnread] = useState(0)
  const [loading, setLoading] = useState(false)
  const ref = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetchUnreadCount()
    const interval = setInterval(fetchUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  async function fetchUnreadCount() {
    try {
      const res = await client.get('/notifications/unread-count')
      setUnread(res.data.count)
    } catch {}
  }

  async function fetchNotifications() {
    setLoading(true)
    try {
      const res = await client.get('/notifications/recent')
      setNotifications(res.data.notifications)
      setUnread(res.data.unread_count)
    } catch {}
    setLoading(false)
  }

  async function markAllRead() {
    await client.post('/notifications/mark-all-read')
    setUnread(0)
    setNotifications(ns => ns.map(n => ({ ...n, is_read: true })))
  }

  async function clickNotif(n) {
    if (!n.is_read) {
      await client.post(`/notifications/${n.id}/mark-read`)
      setUnread(u => Math.max(0, u - 1))
      setNotifications(ns => ns.map(x => x.id === n.id ? { ...x, is_read: true } : x))
    }
    if (n.ticket_id) {
      navigate(`/tickets/${n.ticket_id}`)
      setOpen(false)
    }
  }

  const handleOpen = () => {
    const next = !open
    setOpen(next)
    if (next) fetchNotifications()
  }

  const hasUnread = unread > 0

  return (
    <div className="dropdown" ref={ref}>
      <button
        className={`btn-icon bell-btn`}
        onClick={handleOpen}
        aria-label={hasUnread ? `${unread} unread notifications` : 'Notifications'}
        title={hasUnread ? `${unread} unread notification${unread !== 1 ? 's' : ''}` : 'Notifications'}
      >
        <i
          className={`bi bi-bell-fill${hasUnread ? ' bell-icon--shake' : ''}`}
          style={{ fontSize: 18 }}
        />
        {hasUnread && (
          <span
            className="notif-badge notif-badge--pulse"
            style={{ position: 'absolute', top: 0, right: 0, transform: 'translate(40%,-30%)' }}
          >
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="notif-dropdown">
          <div className="notif-header">
            <span style={{ fontWeight: 600 }}>
              Notifications{hasUnread && <span style={{ color: 'var(--danger)', marginLeft: 6 }}>({unread})</span>}
            </span>
            {hasUnread && (
              <button className="btn-icon" onClick={markAllRead} style={{ fontSize: 12, color: '#3b82f6' }}>
                Mark all read
              </button>
            )}
          </div>
          <div style={{ maxHeight: 360, overflowY: 'auto' }}>
            {loading ? (
              <div style={{ padding: 20, textAlign: 'center' }}><span className="spinner" /></div>
            ) : notifications.length === 0 ? (
              <div style={{ padding: '32px 24px', textAlign: 'center', color: '#9ca3af' }}>
                <i className="bi bi-bell-slash" style={{ fontSize: 28, display: 'block', marginBottom: 8, opacity: 0.4 }} />
                <span style={{ fontSize: 13 }}>No notifications</span>
              </div>
            ) : (
              notifications.map(n => (
                <div key={n.id} className={`notif-item ${!n.is_read ? 'unread' : ''}`} onClick={() => clickNotif(n)}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    <div style={{
                      width: 8, height: 8, borderRadius: '50%', marginTop: 4, flexShrink: 0,
                      background: n.is_read ? 'transparent' : 'var(--primary)',
                      border: n.is_read ? '2px solid var(--gray-300)' : 'none',
                    }} />
                    <div style={{ flex: 1 }}>
                      <div className="notif-title">{n.title}</div>
                      <div className="notif-msg">{n.message}</div>
                      <div className="notif-time">
                        {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          {notifications.length > 0 && (
            <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border)', textAlign: 'center' }}>
              <button
                className="btn btn-secondary btn-sm"
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => { navigate('/notifications/settings'); setOpen(false) }}
              >
                <i className="bi bi-gear" /> Notification Settings
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
