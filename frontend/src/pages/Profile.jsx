import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'
import toast from 'react-hot-toast'
import { RoleBadge } from '../components/StatusBadge'
import { format } from 'date-fns'

function getInitials(name) {
  return (name || 'U').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

export default function Profile() {
  const { user, updateUser } = useAuth()
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [pwLoading, setPwLoading] = useState(false)
  const [pwErrors, setPwErrors] = useState({})

  const handleChangePw = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!pwForm.current_password) errs.current_password = 'Required'
    if (!pwForm.new_password) errs.new_password = 'Required'
    if (pwForm.new_password.length < 6) errs.new_password = 'Min 6 characters'
    if (pwForm.new_password !== pwForm.confirm_password) errs.confirm_password = 'Passwords do not match'
    if (Object.keys(errs).length) { setPwErrors(errs); return }

    setPwLoading(true)
    try {
      await client.put('/auth/change-password', {
        current_password: pwForm.current_password,
        new_password: pwForm.new_password,
      })
      toast.success('Password changed successfully')
      setPwForm({ current_password: '', new_password: '', confirm_password: '' })
      setPwErrors({})
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to change password')
    }
    setPwLoading(false)
  }

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">My Profile</h1>
          <p className="page-subtitle">Your account information</p>
        </div>
      </div>

      {/* Profile Card */}
      <div className="card mb-24">
        <div className="card-body" style={{ display: 'flex', alignItems: 'center', gap: 24, padding: 28 }}>
          <div className="avatar" style={{ width: 72, height: 72, fontSize: 28 }}>{getInitials(user?.full_name)}</div>
          <div>
            <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>{user?.full_name}</h2>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <RoleBadge role={user?.role} />
              <span style={{ fontSize: 13, color: '#6b7280' }}>@{user?.username}</span>
              <span style={{ fontSize: 13, color: '#6b7280' }}>{user?.email}</span>
            </div>
            {user?.created_at && (
              <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 8 }}>
                Member since {format(new Date(user.created_at), 'MMMM d, yyyy')}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Account Details */}
      <div className="card mb-24">
        <div className="card-header"><h3>Account Details</h3></div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {[
              { label: 'Full Name', value: user?.full_name },
              { label: 'Username', value: user?.username },
              { label: 'Email', value: user?.email },
              { label: 'Role', value: <RoleBadge role={user?.role} /> },
              { label: 'Phone', value: user?.phone_number || '—' },
              { label: 'Account Status', value: user?.is_active ? <span style={{ color: '#10b981' }}>Active</span> : <span style={{ color: '#ef4444' }}>Inactive</span> },
            ].map(row => (
              <div key={row.label}>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>{row.label}</div>
                <div style={{ fontSize: 14, fontWeight: 500 }}>{row.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Change Password */}
      <div className="card">
        <div className="card-header"><h3><i className="bi bi-shield-lock" style={{ marginRight: 8 }} />Change Password</h3></div>
        <div className="card-body">
          <form onSubmit={handleChangePw}>
            <div className="form-group">
              <label className="form-label">Current Password *</label>
              <input
                className="form-control"
                type="password"
                value={pwForm.current_password}
                onChange={e => setPwForm(f => ({ ...f, current_password: e.target.value }))}
                autoComplete="current-password"
              />
              {pwErrors.current_password && <div className="form-error">{pwErrors.current_password}</div>}
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">New Password *</label>
                <input
                  className="form-control"
                  type="password"
                  value={pwForm.new_password}
                  onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))}
                  autoComplete="new-password"
                />
                {pwErrors.new_password && <div className="form-error">{pwErrors.new_password}</div>}
              </div>
              <div className="form-group">
                <label className="form-label">Confirm New Password *</label>
                <input
                  className="form-control"
                  type="password"
                  value={pwForm.confirm_password}
                  onChange={e => setPwForm(f => ({ ...f, confirm_password: e.target.value }))}
                  autoComplete="new-password"
                />
                {pwErrors.confirm_password && <div className="form-error">{pwErrors.confirm_password}</div>}
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={pwLoading}>
              {pwLoading ? 'Saving…' : <><i className="bi bi-shield-lock" /> Change Password</>}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
