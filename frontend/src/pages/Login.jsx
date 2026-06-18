import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      const to = user.role === 'admin' ? '/admin' : '/dashboard'
      navigate(to, { replace: true })
    }
  }, [user, navigate])

  const from = location.state?.from?.pathname || null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    const result = await login(form.username, form.password)
    setLoading(false)
    if (result.success) {
      const dest = from || (result.user.role === 'admin' ? '/admin' : '/dashboard')
      navigate(dest, { replace: true })
    } else {
      setError(result.error)
    }
  }

  return (
    <div className="login-page">
      <div className="login-left">
        <h1>Welcome to ICT Helpdesk</h1>
        <p>Your one-stop solution for all ICT support needs. Submit tickets, track issues, and get professional support from our dedicated IT team.</p>
        <div className="login-features">
          <div className="login-feature">
            <i className="bi bi-ticket-detailed-fill" />
            <span>Submit Tickets</span>
          </div>
          <div className="login-feature">
            <i className="bi bi-graph-up-arrow" />
            <span>Track Progress</span>
          </div>
          <div className="login-feature">
            <i className="bi bi-headset" />
            <span>Get Support</span>
          </div>
        </div>
      </div>

      <div className="login-right">
        <div className="login-logo">
          <img src="/static/images/logo.png" alt="University of Nairobi" onError={e => e.target.style.display='none'} />
          <h2>UNIVERSITY OF NAIROBI</h2>
          <p>USER LOGIN</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && <div className="alert alert-danger"><i className="bi bi-exclamation-circle" /> {error}</div>}

          <div className="form-group">
            <label className="form-label">Username / Payroll Number</label>
            <div style={{ position: 'relative' }}>
              <i className="bi bi-person" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
              <input
                className="form-control"
                style={{ paddingLeft: 36 }}
                placeholder="Enter your username"
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                required
                autoComplete="username"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div style={{ position: 'relative' }}>
              <i className="bi bi-lock" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
              <input
                className="form-control"
                style={{ paddingLeft: 36 }}
                type="password"
                placeholder="Enter your password"
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary w-100 btn-lg"
            style={{ marginTop: 8, justifyContent: 'center' }}
            disabled={loading}
          >
            {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Signing in…</> : 'Sign In'}
          </button>

          <div style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: '#6b7280' }}>
            Contact your administrator for account access
          </div>
        </form>
      </div>
    </div>
  )
}
