import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'
import { RoleBadge } from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

function CreateUserModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ username: '', email: '', full_name: '', password: '', role: 'user' })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await client.post('/users', form)
      onCreated(res.data)
      toast.success('User created')
      onClose()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create user')
    }
    setLoading(false)
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3>Create User</h3>
          <button className="btn-icon" onClick={onClose}><i className="bi bi-x-lg" /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Username *</label>
                <input className="form-control" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label className="form-label">Full Name *</label>
                <input className="form-control" value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} required />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Email *</label>
              <input className="form-control" type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Password *</label>
                <input className="form-control" type="password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required minLength={6} />
              </div>
              <div className="form-group">
                <label className="form-label">Role</label>
                <select className="form-control" value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
                  <option value="user">User</option>
                  <option value="intern">Intern</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-outline btn-sm" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary btn-sm" disabled={loading}>
              {loading ? 'Creating…' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ResetPasswordModal({ user, onClose }) {
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await client.post(`/users/${user.id}/reset-password`, { new_password: password })
      toast.success('Password reset')
      onClose()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed')
    }
    setLoading(false)
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3>Reset Password — {user.full_name}</h3>
          <button className="btn-icon" onClick={onClose}><i className="bi bi-x-lg" /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">New Password *</label>
              <input className="form-control" type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-outline btn-sm" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary btn-sm" disabled={loading}>{loading ? 'Saving…' : 'Reset'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function UserManagement() {
  const [users, setUsers] = useState([])
  const [meta, setMeta] = useState({ total: 0, pages: 1, current_page: 1 })
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [resetTarget, setResetTarget] = useState(null)

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, per_page: 20 }
      if (search) params.search = search
      if (roleFilter) params.role = roleFilter
      const res = await client.get('/users', { params })
      setUsers(res.data.users)
      setMeta({ total: res.data.total, pages: res.data.pages, current_page: res.data.current_page })
    } catch {}
    setLoading(false)
  }, [search, roleFilter, page])

  useEffect(() => { fetchUsers() }, [fetchUsers])

  async function toggleStatus(user) {
    try {
      const res = await client.post(`/users/${user.id}/toggle-status`)
      setUsers(us => us.map(u => u.id === user.id ? { ...u, is_active: res.data.is_active } : u))
      toast.success(`User ${res.data.is_active ? 'activated' : 'deactivated'}`)
    } catch { toast.error('Failed') }
  }

  async function approveUser(user) {
    try {
      const res = await client.post(`/users/${user.id}/approve`)
      setUsers(us => us.map(u => u.id === user.id ? res.data : u))
      toast.success('User approved')
    } catch { toast.error('Failed') }
  }

  async function deleteUser(user) {
    if (!confirm(`Delete ${user.full_name}?`)) return
    try {
      await client.delete(`/users/${user.id}`)
      setUsers(us => us.filter(u => u.id !== user.id))
      toast.success('User deleted')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed')
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">User Management</h1>
          <p className="page-subtitle">{meta.total} users total</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <i className="bi bi-person-plus" /> Create User
        </button>
      </div>

      {showCreate && <CreateUserModal onClose={() => setShowCreate(false)} onCreated={u => setUsers(us => [u, ...us])} />}
      {resetTarget && <ResetPasswordModal user={resetTarget} onClose={() => setResetTarget(null)} />}

      <div className="card mb-16">
        <div className="card-body" style={{ padding: '12px 16px' }}>
          <div className="filter-bar">
            <input className="form-control search-input" placeholder="Search users…" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} />
            <select className="form-control" value={roleFilter} onChange={e => { setRoleFilter(e.target.value); setPage(1) }}>
              <option value="">All Roles</option>
              <option value="admin">Admin</option>
              <option value="intern">Intern</option>
              <option value="user">User</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? <LoadingSpinner text="Loading users…" /> : (
        <>
          <div className="table-container">
            <table>
              <thead>
                <tr><th>User</th><th>Role</th><th>Status</th><th>Approved</th><th>Joined</th><th style={{ textAlign: 'right' }}>Actions</th></tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{u.full_name}</div>
                      <div style={{ fontSize: 12, color: '#6b7280' }}>@{u.username} · {u.email}</div>
                    </td>
                    <td><RoleBadge role={u.role} /></td>
                    <td>
                      <span className={`badge ${u.is_active ? 'badge-resolved' : 'badge-closed'}`}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      {u.is_approved
                        ? <span className="badge badge-resolved">Approved</span>
                        : <span className="badge badge-in_progress">Pending</span>}
                    </td>
                    <td style={{ fontSize: 12, color: '#6b7280' }}>
                      {u.created_at ? format(new Date(u.created_at), 'MMM d, yyyy') : '—'}
                    </td>
                    <td>
                      <div className="flex gap-8" style={{ justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                        {!u.is_approved && u.role === 'intern' && (
                          <button className="btn btn-success btn-sm" onClick={() => approveUser(u)}>
                            <i className="bi bi-check" /> Approve
                          </button>
                        )}
                        <button className="btn btn-outline btn-sm" onClick={() => toggleStatus(u)}>
                          {u.is_active ? <><i className="bi bi-pause" /> Deactivate</> : <><i className="bi bi-play" /> Activate</>}
                        </button>
                        <button className="btn btn-secondary btn-sm" onClick={() => setResetTarget(u)}>
                          <i className="bi bi-key" /> Reset PW
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => deleteUser(u)}>
                          <i className="bi bi-trash" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {meta.pages > 1 && (
            <div className="pagination">
              <button className="page-btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><i className="bi bi-chevron-left" /></button>
              {Array.from({ length: meta.pages }, (_, i) => i + 1).map(p => (
                <button key={p} className={`page-btn ${p === page ? 'active' : ''}`} onClick={() => setPage(p)}>{p}</button>
              ))}
              <button className="page-btn" disabled={page >= meta.pages} onClick={() => setPage(p => p + 1)}><i className="bi bi-chevron-right" /></button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
