export default function LoadingSpinner({ size = 'md', text = '' }) {
  return (
    <div className="loading-center" style={{ flexDirection: 'column', gap: 12 }}>
      <span className={`spinner ${size === 'lg' ? 'spinner-lg' : ''}`} />
      {text && <span style={{ color: '#6b7280', fontSize: 14 }}>{text}</span>}
    </div>
  )
}
