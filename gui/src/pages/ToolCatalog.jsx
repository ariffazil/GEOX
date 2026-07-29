import { useState, useEffect } from 'react'
import { fetchToolsList } from '../api.js'

const EXCLUDED_TOOLS = new Set([
  'geox_geological_model_generate', // shown separately
])

export default function ToolCatalog() {
  const [tools, setTools] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchToolsList()
      .then(list => {
        const filtered = list.filter(t => !EXCLUDED_TOOLS.has(t.name))
        setTools(filtered)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const filtered = tools.filter(t => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      t.name.toLowerCase().includes(q) ||
      (t.description || '').toLowerCase().includes(q)
    )
  })

  function domainLabel(name) {
    if (name.includes('basin')) return 'basin'
    if (name.includes('seismic')) return 'seismic'
    if (name.includes('well')) return 'well'
    if (name.includes('map')) return 'map'
    if (name.includes('petrophysics') || name.includes('lem')) return 'petrophysics'
    if (name.includes('claim') || name.includes('falsify') || name.includes('contradiction')) return 'governance'
    if (name.includes('prospect') || name.includes('wealth')) return 'economics'
    if (name.includes('sequence') || name.includes('sediment') || name.includes('thermal')) return 'stratigraphy'
    if (name.includes('surface_status')) return 'system'
    if (name.includes('workspace')) return 'workspace'
    if (name.includes('geomechanics') || name.includes('gravmag') || name.includes('subsurface')) return 'geophysics'
    if (name.includes('visual')) return 'ml'
    return 'general'
  }

  return (
    <div>
      <div className="page-header">
        <h1>Φ GEOX Tool Catalog</h1>
        <p>All {tools.length} public GEOX earth-intelligence tools</p>
      </div>

      <input
        className="search-box"
        placeholder="Search tools by name or description..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <div className="spinner" style={{ margin: '0 auto 12px' }} />
          <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading tool catalog...</div>
        </div>
      )}

      {error && (
        <div className="alert error">
          Failed to load tools: {error}
        </div>
      )}

      {!loading && !error && (
        <>
          <div style={{ marginBottom: 12, fontSize: 13, color: 'var(--text-muted)' }}>
            {filtered.length} of {tools.length} tools shown
          </div>
          <div className="tool-grid">
            {filtered.map(t => (
              <div key={t.name} className="tool-card">
                <div className="tool-card-header">
                  <span className="tool-name">{t.name}</span>
                  <span className="tool-domain">{domainLabel(t.name)}</span>
                </div>
                <div className="tool-description">
                  {t.description || 'No description available'}
                </div>
                <div className="tool-tags">
                  {t.inputSchema?.properties && Object.keys(t.inputSchema.properties).slice(0, 4).map(k => (
                    <span key={k} className="tool-tag">{k}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
