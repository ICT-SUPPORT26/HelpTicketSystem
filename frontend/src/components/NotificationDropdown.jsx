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

  return (
    <div className="dropdown" ref={ref}>
      <button className="btn-icon" onClick={handleOpen} style={{ position: 'relative' }}>
        <i className="bi bi-bell-fill" style={{ fontSize: 18 }} />
        {unread > 0 && (
          <span className="notif-badge" style={{ position: 'absolute', top: 0, right: 0, transform: 'translate(40%,-30%)' }}>
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="notif-dropdown">
          <div className="notif-header">
            <span style={{ fontWeight: 600 }}>Notifications {unread > 0 && `(${unread})`}</span>
            <button className="btn-icon" onClick={markAllRead} style={{ fontSize: 12, color: '#3b82f6' }}>
              Mark all read
            </button>
          </div>
          <div style={{ maxHeight: 360, overflowY: 'auto' }}>
            {loading ? (
              <div style={{ padding: 20, textAlign: 'center' }}><span className="spinner" /></div>
            ) : notifications.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>
                No notifications
              </div>
            ) : (
              notifications.map(n => (
                <div key={n.id} className={`notif-item ${!n.is_read ? 'unread' : ''}`} onClick={() => clickNotif(n)}>
                  <div className="notif-title">{n.title}</div>
                  <div className="notif-msg">{n.message}</div>
                  <div className="notif-time">
                    {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
