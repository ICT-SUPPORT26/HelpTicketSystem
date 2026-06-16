import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import { PrivateRoute, AdminRoute, StaffRoute } from './routes/PrivateRoute'
import MainLayout from './layouts/MainLayout'

import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import AdminDashboard from './pages/AdminDashboard'
import TicketList from './pages/TicketList'
import TicketDetail from './pages/TicketDetail'
import TicketForm from './pages/TicketForm'
import UserManagement from './pages/UserManagement'
import Reports from './pages/Reports'
import Analytics from './pages/Analytics'
import Profile from './pages/Profile'
import NotificationSettings from './pages/NotificationSettings'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Toaster position="top-right" toastOptions={{ duration: 4000 }} />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route element={<PrivateRoute><MainLayout /></PrivateRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/tickets" element={<TicketList />} />
            <Route path="/tickets/new" element={<TicketForm />} />
            <Route path="/tickets/:id" element={<TicketDetail />} />
            <Route path="/tickets/:id/edit" element={<TicketForm />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/notifications/settings" element={<NotificationSettings />} />

            <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
            <Route path="/admin/users" element={<AdminRoute><UserManagement /></AdminRoute>} />
            <Route path="/reports" element={<StaffRoute><Reports /></StaffRoute>} />
            <Route path="/analytics" element={<AdminRoute><Analytics /></AdminRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
