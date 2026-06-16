import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

const LOCATIONS = [
  'Main Campus - Administration Block', 'Main Campus - Library', 'Main Campus - IT Department',
  'Main Campus - Science Block', 'Main Campus - Arts Block', 'Main Campus - Engineering',
  'Chiromo Campus', 'Parklands Campus', 'Lower Kabete Campus', 'Medical School',
  'SWA', 'UHS', 'Confucius Institute', 'Other',
]

export default function TicketForm() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const { user } = useAuth()

  const [form, setForm] = useState({ location: '', description: '', priority: 'medium', category_id: '', assignees: [] })
  const [files, setFiles] = useState([])
  const [categories, setCategories] = useState([])
  const [staff, setStaff] = useState([])
  const [loading, setLoading] = useState(false)
  const [fetchingTicket, setFetchingTicket] = useState(isEdit)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    client.get('/categories').then(r => setCategories(r.data)).catch(() => {})
    if (user.role === 'admin' || user.role === 'intern') {
      client.get('/users/staff').then(r => setStaff(r.data)).catch(() => {})
    }
    if (isEdit) {
      client.get(`/tickets/${id}`).then(r => {
        const t = r.data
        setForm({
          location: t.location,
          description: t.description,
          priority: t.priority,
          category_id: t.category?.id || '',
          assignees: t.assignees?.map(a => a.id) || [],
        })
        setFetchingTicket(false)
      }).catch(() => navigate('/tickets'))
    }
  }, [id])

  const validate = () => {
    const errs = {}
    if (!form.location) errs.location = 'Location is required'
    if (!form.description.trim()) errs.description = 'Description is required'
    return errs
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setLoading(true)
    try {
      if (files.length > 0) {
        const fd = new FormData()
        fd.append('location', form.location)
        fd.append('description', form.description)
        fd.append('priority', form.priority)
        if (form.category_id) fd.append('category_id', form.category_id)
        form.assignees.forEach(a => fd.append('assignees', a))
        files.forEach(f => fd.append('attachments', f))
        if (isEdit) {
          await client.put(`/tickets/${id}`, form)
        } else {
          const res = await client.post('/tickets', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
          navigate(`/tickets/${res.data.id}`)
        }
      } else {
        if (isEdit) {
          await client.put(`/tickets/${id}`, form)
          navigate(`/tickets/${id}`)
        } else {
          const res = await client.post('/tickets', form)
          navigate(`/tickets/${res.data.id}`)
        }
      }
      toast.success(isEdit ? 'Ticket updated' : 'Ticket created successfully')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to save ticket')
    }
    setLoading(false)
  }

  if (fetchingTicket) return <div className="loading-center"><span className="spinner spinner-lg" /></div>

  return (
    <div style={{ maxWidth: 760, margin: '0 auto' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">{isEdit ? 'Edit Ticket' : 'Create New Ticket'}</h1>
          <p className="page-subtitle">{isEdit ? `Editing ticket #${id}` : 'Submit a new support request'}</p>
        </div>
        <button className="btn btn-outline btn-sm" onClick={() => navigate(isEdit ? `/tickets/${id}` : '/tickets')}>
          <i className="bi bi-arrow-left" /> Cancel
        </button>
      </div>

      <div className="card">
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Location *</label>
              <select
                className="form-control"
                value={form.location}
                onChange={e => { setForm(f => ({ ...f, location: e.target.value })); setErrors(e2 => ({ ...e2, location: '' })) }}
              >
                <option value="">Select location…</option>
                {LOCATIONS.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
              {errors.location && <div className="form-error">{errors.location}</div>}
            </div>

            <div className="form-group">
              <label className="form-label">Description *</label>
              <textarea
                className="form-control"
                placeholder="Describe the issue in detail…"
                rows={5}
                value={form.description}
                onChange={e => { setForm(f => ({ ...f, description: e.target.value })); setErrors(e2 => ({ ...e2, description: '' })) }}
              />
              {errors.description && <div className="form-error">{errors.description}</div>}
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Priority</label>
                <select className="form-control" value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Category</label>
                <select className="form-control" value={form.category_id} onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}>
                  <option value="">No Category</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            </div>

            {(user.role === 'admin' || user.role === 'intern') && staff.length > 0 && (
              <div className="form-group">
                <label className="form-label">Assign To (hold Ctrl/Cmd to select multiple)</label>
                <select
                  className="form-control"
                  multiple
                  value={form.assignees.map(String)}
                  onChange={e => setForm(f => ({ ...f, assignees: Array.from(e.target.selectedOptions, o => parseInt(o.value)) }))}
                  style={{ minHeight: 100 }}
                >
                  {staff.map(s => <option key={s.id} value={s.id}>{s.full_name} ({s.role})</option>)}
                </select>
              </div>
            )}

            <div className="form-group">
              <label className="form-label">{isEdit ? 'Add Attachments' : 'Attachments'}</label>
              <input
                type="file"
                className="form-control"
                multiple
                accept=".txt,.pdf,.png,.jpg,.jpeg,.gif,.doc,.docx,.xls,.xlsx"
                onChange={e => setFiles(Array.from(e.target.files))}
              />
              <div className="form-hint">Allowed: PDF, images, Word, Excel (max 16MB each)</div>
              {files.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  {files.map(f => <div key={f.name} style={{ fontSize: 12, color: '#6b7280' }}><i className="bi bi-paperclip" /> {f.name}</div>)}
                </div>
              )}
            </div>

            <div className="flex gap-8" style={{ marginTop: 8 }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Saving…</> : (isEdit ? 'Save Changes' : 'Submit Ticket')}
              </button>
              <button type="button" className="btn btn-outline" onClick={() => navigate(isEdit ? `/tickets/${id}` : '/tickets')}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
