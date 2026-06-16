import { useState, useEffect } from 'react'
import client from '../api/client'
import toast from 'react-hot-toast'
import LoadingSpinner from '../components/LoadingSpinner'

function Toggle({ checked, onChange }) {
  return (
    <label className="toggle">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
      <span className="toggle-track" />
      <span className="toggle-thumb" />
    </label>
  )
}

const settingGroups = [
  {
    label: 'New Ticket',
    emailKey: 'new_ticket_email',
    appKey: 'new_ticket_app',
  },
  {
    label: 'Ticket Updated',
    emailKey: 'ticket_updated_email',
    appKey: 'ticket_updated_app',
  },
  {
    label: 'New Comment',
    emailKey: 'new_comment_email',
    appKey: 'new_comment_app',
  },
  {
    label: 'Ticket Closed',
    emailKey: 'ticket_closed_email',
    appKey: 'ticket_closed_app',
  },
  {
    label: 'Ticket Overdue',
    emailKey: 'ticket_overdue_email',
    appKey: 'ticket_overdue_app',
  },
]

export default function NotificationSettings() {
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    client.get('/notifications/settings').then(r => { setSettings(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      await client.put('/notifications/settings', settings)
      toast.success('Settings saved')
    } catch {
      toast.error('Failed to save settings')
    }
    setSaving(false)
  }

  const update = (key, val) => setSettings(s => ({ ...s, [key]: val }))

  if (loading) return <LoadingSpinner text="Loading settings…" />
  if (!settings) return null

  return (
    <div style={{ maxWidth: 680, margin: '0 auto' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Notification Settings</h1>
          <p className="page-subtitle">Choose how you want to be notified</p>
        </div>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving…' : <><i className="bi bi-check-circle" /> Save Settings</>}
        </button>
      </div>

      <div className="card mb-24">
        <div className="card-header"><h3>Email & In-App Notifications</h3></div>
        <div className="card-body" style={{ padding: 0 }}>
          <table style={{ width: '100%' }}>
            <thead>
              <tr>
                <th style={{ padding: '12px 20px', textAlign: 'left', fontSize: 12, color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase' }}>Event</th>
                <th style={{ padding: '12px 20px', textAlign: 'center', fontSize: 12, color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase' }}>Email</th>
                <th style={{ padding: '12px 20px', textAlign: 'center', fontSize: 12, color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase' }}>In-App</th>
              </tr>
            </thead>
            <tbody>
              {settingGroups.map(g => (
                <tr key={g.label} style={{ borderTop: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '14px 20px', fontWeight: 500 }}>{g.label}</td>
                  <td style={{ padding: '14px 20px', textAlign: 'center' }}>
                    <Toggle checked={!!settings[g.emailKey]} onChange={v => update(g.emailKey, v)} />
                  </td>
                  <td style={{ padding: '14px 20px', textAlign: 'center' }}>
                    <Toggle checked={!!settings[g.appKey]} onChange={v => update(g.appKey, v)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><h3>Do Not Disturb</h3></div>
        <div className="card-body">
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
            <Toggle checked={!!settings.do_not_disturb} onChange={v => update('do_not_disturb', v)} />
            <div>
              <div style={{ fontWeight: 500 }}>Enable Do Not Disturb</div>
              <div style={{ fontSize: 13, color: '#6b7280' }}>Suppress notifications during specified hours</div>
            </div>
          </div>
          {settings.do_not_disturb && (
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Start Time</label>
                <input type="time" className="form-control" value={settings.dnd_start_time || ''} onChange={e => update('dnd_start_time', e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">End Time</label>
                <input type="time" className="form-control" value={settings.dnd_end_time || ''} onChange={e => update('dnd_end_time', e.target.value)} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
