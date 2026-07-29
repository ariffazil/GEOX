import { useState } from 'react'
import { mcpCall } from '../api.js'

const DEFAULT_COLORS = ['#d4a574', '#b8c9a0', '#8ab8d4', '#c9a87c', '#a0b8c9', '#74695e', '#4a4a4a']

export default function CrossSectionBuilder() {
  const [params, setParams] = useState({
    grid_width_m: 2000,
    grid_depth_m: 1000,
    dip_angle_deg: 0,
    fault_throw_m: 0,
    title: 'Geological Cross-Section',
  })
  const [strata, setStrata] = useState([
    { name: 'Layer A', thickness_m: 200, color: '#d4a574' },
    { name: 'Layer B', thickness_m: 150, color: '#b8c9a0' },
    { name: 'Layer C', thickness_m: 100, color: '#8ab8d4' },
    { name: 'Layer D', thickness_m: 80, color: '#c9a87c' },
    { name: 'Layer E', thickness_m: 60, color: '#a0b8c9' },
    { name: 'Layer F', thickness_m: 40, color: '#74695e' },
    { name: 'Basement', thickness_m: 20, color: '#4a4a4a' },
  ])
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  function addLayer() {
    const idx = strata.length
    setStrata([...strata, {
      name: `Layer ${String.fromCharCode(65 + idx)}`,
      thickness_m: 50,
      color: DEFAULT_COLORS[idx % DEFAULT_COLORS.length],
    }])
  }

  function removeLayer(idx) {
    if (strata.length <= 2) return
    setStrata(strata.filter((_, i) => i !== idx))
  }

  function updateStrata(idx, field, value) {
    const updated = [...strata]
    updated[idx] = { ...updated[idx], [field]: field === 'thickness_m' ? Number(value) : value }
    setStrata(updated)
  }

  async function generate() {
    setLoading(true)
    setError(null)
    setPreview(null)
    try {
      const result = await mcpCall('geox_geological_model_generate', {
        params: {
          ...params,
          grid_width_m: Number(params.grid_width_m),
          grid_depth_m: Number(params.grid_depth_m),
          dip_angle_deg: Number(params.dip_angle_deg),
          fault_throw_m: Number(params.fault_throw_m),
          strata,
        },
      })
      // Result is a JSON string with image_path
      let parsed = result
      if (typeof result.content?.[0]?.text === 'string') {
        parsed = JSON.parse(result.content[0].text)
      } else if (typeof result === 'string') {
        parsed = JSON.parse(result)
      }
      const imagePath = parsed.image_path || parsed.result?.image_path || result.image_path
      if (imagePath) {
        setPreview(`/geox-preview?path=${encodeURIComponent(imagePath)}&t=${Date.now()}`)
      } else {
        setError('No image path returned. Raw result: ' + JSON.stringify(result).slice(0, 200))
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>⬡ Cross-Section Builder</h1>
        <p>Configure structural parameters and stratigraphy to generate a deterministic 2D geological cross-section</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div>
          <div className="card">
            <div className="card-title">Structural Parameters</div>
            <div className="form-row">
              <div className="form-group">
                <label>Width (m)</label>
                <input type="number" value={params.grid_width_m}
                  onChange={e => setParams({...params, grid_width_m: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Depth (m)</label>
                <input type="number" value={params.grid_depth_m}
                  onChange={e => setParams({...params, grid_depth_m: e.target.value})} />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Dip Angle (°)</label>
                <input type="number" value={params.dip_angle_deg} step="5"
                  onChange={e => setParams({...params, dip_angle_deg: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Fault Throw (m)</label>
                <input type="number" value={params.fault_throw_m} step="10"
                  onChange={e => setParams({...params, fault_throw_m: e.target.value})} />
              </div>
            </div>
            <div className="form-group">
              <label>Title</label>
              <input type="text" value={params.title}
                onChange={e => setParams({...params, title: e.target.value})} />
            </div>
          </div>

          <div className="card">
            <div className="card-title">
              Strata Layers
              <button className="btn btn-secondary" style={{ float: 'right', padding: '4px 12px', fontSize: 12 }}
                onClick={addLayer}>+ Add Layer</button>
            </div>
            <div className="strata-list">
              {strata.map((s, i) => (
                <div key={i} className="strata-item">
                  <input placeholder="Name" value={s.name}
                    onChange={e => updateStrata(i, 'name', e.target.value)} />
                  <input type="number" placeholder="Thickness (m)" value={s.thickness_m} min="1"
                    onChange={e => updateStrata(i, 'thickness_m', e.target.value)}
                    style={{ width: 100 }} />
                  <input type="color" value={s.color}
                    onChange={e => updateStrata(i, 'color', e.target.value)} />
                  {strata.length > 2 && (
                    <button className="btn-remove" onClick={() => removeLayer(i)}>✕</button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <button className="btn" onClick={generate} disabled={loading} style={{ width: '100%' }}>
            {loading ? <><span className="spinner" /> Generating...</> : 'Generate Cross-Section'}
          </button>
        </div>

        <div>
          <div className="card">
            <div className="card-title">Preview</div>
            {error && <div className="alert error">{error}</div>}
            {!preview && !error && (
              <div className="chart-container">
                Configure parameters and click Generate
              </div>
            )}
            {preview && (
              <div className="preview-container">
                <img src={preview} alt="Geological cross-section"
                  onError={() => setPreview(null)} />
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-title">Parameters Summary</div>
            <pre style={{
              fontSize: 12,
              color: 'var(--text-secondary)',
              fontFamily: "'SF Mono', 'Fira Code', monospace",
              whiteSpace: 'pre-wrap',
              background: 'var(--bg-input)',
              padding: 12,
              borderRadius: 'var(--radius-sm)',
            }}>
{JSON.stringify({ ...params, strata: strata.map(s => ({ name: s.name, thickness_m: s.thickness_m, color: s.color })) }, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
