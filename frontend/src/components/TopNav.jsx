import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import NotificationDropdown from './NotificationDropdown'

const breadcrumbs = {
  '/dashboard': 'Dashboard',
  '/tickets': 'Tickets',
  '/tickets/new': 'New Ticket',
  '/admin': 'Admin Dashboard',
  '/admin/users': 'User Management',
  '/reports': 'Reports',
  '/analytics': 'Analytics',
  '/profile': 'My Profile',
  '/notifications/settings': 'Notification Settings',
}

function getInitials(name) {
  if (!name) return 'U'
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

export default function TopNav() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  const path = location.pathname
  const label = Object.entries(breadcrumbs).find(([k]) => path === k || path.startsWith(k + '/'))?.[1] || 'Page'

  useEffect(() => {
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="topnav">
      <div className="topnav-left">
        <div className="topnav-breadcrumb">
          ICT Helpdesk &rsaquo; <span>{label}</span>
        </div>
      </div>

      <div className="topnav-right">
        <NotificationDropdown />

        <div className="dropdown" ref={menuRef}>
          <button
            className="btn-icon flex gap-8"
            onClick={() => setMenuOpen(o => !o)}
            style={{ gap: 8, padding: '4px 8px' }}
          >
            <div className="avatar">
              {getInitials(user?.full_name)}
            </div>
            <span style={{ fontSize: 13, fontWeight: 500 }}>{user?.full_name?.split(' ')[0]}</span>
            <i className="bi bi-chevron-down" style={{ fontSize: 11 }} />
          </button>
          {menuOpen && (
            <div className="dropdown-menu">
              <div style={{ padding: '10px 16px', borderBottom: '1px solid #e5e7eb' }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{user?.full_name}</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>{user?.role}</div>
              </div>
              <div className="dropdown-item" onClick={() => { navigate('/profile'); setMenuOpen(false) }}>
                <i className="bi bi-person" /> My Profile
              </div>
              <div className="dropdown-item" onClick={() => { navigate('/notifications/settings'); setMenuOpen(false) }}>
                <i className="bi bi-bell" /> Notifications
              </div>
              <div className="dropdown-divider" />
              <div className="dropdown-item danger" onClick={handleLogout}>
                <i className="bi bi-box-arrow-right" /> Sign Out
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
