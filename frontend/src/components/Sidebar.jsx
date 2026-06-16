import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { section: 'Main', items: [
    { to: '/dashboard', icon: 'bi-grid-1x2-fill', label: 'Dashboard', roles: ['admin', 'intern', 'user'] },
    { to: '/tickets', icon: 'bi-ticket-detailed-fill', label: 'Tickets', roles: ['admin', 'intern', 'user'] },
    { to: '/tickets/new', icon: 'bi-plus-circle-fill', label: 'New Ticket', roles: ['admin', 'intern', 'user'] },
  ]},
  { section: 'Admin', items: [
    { to: '/admin', icon: 'bi-speedometer2', label: 'Admin Dashboard', roles: ['admin'] },
    { to: '/admin/users', icon: 'bi-people-fill', label: 'User Management', roles: ['admin'] },
    { to: '/admin/interns', icon: 'bi-person-badge-fill', label: 'Intern Management', roles: ['admin'] },
  ]},
  { section: 'Reports', items: [
    { to: '/reports', icon: 'bi-bar-chart-fill', label: 'Reports', roles: ['admin', 'intern'] },
    { to: '/analytics', icon: 'bi-graph-up-arrow', label: 'Analytics', roles: ['admin'] },
  ]},
  { section: 'Account', items: [
    { to: '/profile', icon: 'bi-person-fill', label: 'My Profile', roles: ['admin', 'intern', 'user'] },
    { to: '/notifications/settings', icon: 'bi-bell-fill', label: 'Notifications', roles: ['admin', 'intern', 'user'] },
  ]},
]

export default function Sidebar({ collapsed, onToggle }) {
  const { user } = useAuth()

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-logo">
        <img src="/static/images/logo.png" alt="logo" onError={e => { e.target.style.display='none' }} />
        {!collapsed && (
          <div>
            <div className="sidebar-logo-text">ICT Helpdesk</div>
            <div className="sidebar-logo-sub">University of Nairobi</div>
          </div>
        )}
      </div>

      <nav className="sidebar-nav">
        {navItems.map(section => {
          const visible = section.items.filter(i => i.roles.includes(user?.role))
          if (!visible.length) return null
          return (
            <div key={section.section}>
              {!collapsed && <div className="nav-section-label">{section.section}</div>}
              {visible.map(item => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/dashboard' || item.to === '/admin'}
                  className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                  <i className={`bi ${item.icon}`} />
                  {!collapsed && <span>{item.label}</span>}
                </NavLink>
              ))}
            </div>
          )
        })}
      </nav>

      <div className="sidebar-footer">
        <button className="sidebar-toggle-btn" onClick={onToggle} title={collapsed ? 'Expand' : 'Collapse'}>
          <i className={`bi ${collapsed ? 'bi-chevron-double-right' : 'bi-chevron-double-left'}`} />
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  )
}
