import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import TopNav from '../components/TopNav'

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="app-layout">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />
      <div className={`main-content ${collapsed ? 'sidebar-collapsed' : ''}`}>
        <TopNav />
        <div className="page-content">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
