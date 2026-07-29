import { useState, useRef, useCallback } from 'react'

function parseLAS(content) {
  const lines = content.split('\n')
  const header = { startDepth: null, endDepth: null, step: null, nullValue: -999.25 }
  const curveInfo = []
  const asciiData = []
  let inAscii = false
  let inCurve = false
  let inWell = false
  let inParam = false
  let curveLine = null

  for (const rawLine of lines) {
    const line = rawLine.replace(/\r$/, '')
    if (line.startsWith('~V') || line.startsWith('~O') || line.startsWith('~O')) continue
    if (line.startsWith('~W')) { inWell = true; inCurve = false; inAscii = false; continue }
    if (line.startsWith('~C')) { inCurve = true; inWell = false; inAscii = false; continue }
    if (line.startsWith('~P')) { inParam = true; inCurve = false; inAscii = false; continue }
    if (line.startsWith('~A')) { inAscii = true; inCurve = false; inWell = false; inParam = false; continue }

    if (inWell) {
      const m = line.match(/^STRT\.?\s+\.?([\d.eE+-]+)/)
      if (m) header.startDepth = parseFloat(m[1])
      const m2 = line.match(/^STOP\.?\s+\.?([\d.eE+-]+)/)
      if (m2) header.endDepth = parseFloat(m2[1])
      const m3 = line.match(/^STEP\.?\s+\.?([\d.eE+-]+)/)
      if (m3) header.step = parseFloat(m3[1])
      const m4 = line.match(/^NULL\.?\s+\.?([\d.eE+-]+)/)
      if (m4) header.nullValue = parseFloat(m4[1])
    }

    if (inCurve) {
      if (line.trim().startsWith('#')) continue
      // Curve definition: NAME.UNIT  :  DESCRIPTION
      const cm = line.match(/^([\w-]+)\.(\w+)?\s*/)
      if (cm) {
        curveInfo.push({
          name: cm[1],
          unit: cm[2] || '',
          values: [],
        })
      }
      // Try fallback: just capture the first token before .
      const cm2 = line.match(/^\.?(\w[\w-]*)/)
      if (!cm && cm2) {
        curveInfo.push({ name: cm2[1], unit: '', values: [] })
      }
    }

    if (inAscii) {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#')) {
        const parts = trimmed.split(/\s+/).map(Number)
        asciiData.push(parts)
      }
    }
  }

  // If no curve info was extracted from ~C, try headers
  if (curveInfo.length === 0 && asciiData.length > 0) {
    const numCols = asciiData[0].length
    for (let i = 0; i < numCols; i++) {
      curveInfo.push({ name: `CURVE_${i + 1}`, unit: '', values: [] })
    }
  }

  // Populate curve values
  for (let row = 0; row < asciiData.length; row++) {
    for (let col = 0; col < curveInfo.length; col++) {
      if (col < asciiData[row].length) {
        const val = asciiData[row][col]
        curveInfo[col].values.push(val === header.nullValue || isNaN(val) ? null : val)
      }
    }
  }

  const depthCol = curveInfo[0]?.name?.toLowerCase().includes('dept') ? 0 : -1
  const depthValues = depthCol >= 0 ? curveInfo[depthCol].values : null

  return { header, curveInfo, asciiData, depthValues }
}

export default function WellLogViewer() {
  const [file, setFile] = useState(null)
  const [parsed, setParsed] = useState(null)
  const [error, setError] = useState(null)
  const [selectedCurve, setSelectedCurve] = useState(null)
  const inputRef = useRef(null)

  const handleFile = useCallback(async (f) => {
    setFile(f)
    setError(null)
    setParsed(null)
    setSelectedCurve(null)
    try {
      const text = await f.text()
      const result = parseLAS(text)
      if (result.curveInfo.length === 0) {
        setError('Could not parse LAS file — no curves found')
        return
      }
      setParsed(result)
      // Auto-select first non-depth curve
      const idx = result.curveInfo.findIndex(c => !c.name.toLowerCase().includes('dept') && c.values.some(v => v !== null))
      setSelectedCurve(idx >= 0 ? idx : 1)
    } catch (e) {
      setError(`Parse error: ${e.message}`)
    }
  }, [])

  function renderChart(curve) {
    const depth = parsed.depthValues || Array.from({ length: curve.values.length }, (_, i) => i)
    const valid = curve.values.map((v, i) => v !== null && depth[i] !== null)
    const points = valid.reduce((acc, ok, i) => {
      if (ok) acc.push({ d: depth[i], v: curve.values[i] })
      return acc
    }, [])

    if (points.length === 0) return <div className="chart-container">No valid data</div>

    const pad = 0.05
    const dMin = Math.min(...points.map(p => p.d))
    const dMax = Math.max(...points.map(p => p.d))
    const vMin = Math.min(...points.map(p => p.v))
    const vMax = Math.max(...points.map(p => p.v))
    const dRange = dMax - dMin || 1
    const vRange = vMax - vMin || 1

    const w = 700, h = 500
    const margin = { top: 20, right: 20, bottom: 40, left: 60 }
    const pw = w - margin.left - margin.right
    const ph = h - margin.top - margin.bottom

    // SVG: depth on Y axis (increasing down), value on X axis
    const x = v => margin.left + ((v - vMin) / vRange) * pw
    const y = d => margin.top + ((dMax - d) / dRange) * ph

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(p.v).toFixed(1)},${y(p.d).toFixed(1)}`).join(' ')

    // Depth ticks
    const nTicks = 10
    const tickStep = dRange / nTicks
    const depthTicks = Array.from({ length: nTicks + 1 }, (_, i) => dMin + i * tickStep)

    return (
      <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', maxHeight: 500 }}>
        <rect x="0" y="0" width={w} height={h} fill="var(--bg-input)" />
        {/* Grid lines */}
        {depthTicks.map((d, i) => (
          <g key={i}>
            <line x1={margin.left} y1={y(d)} x2={w - margin.right} y2={y(d)}
              stroke="var(--border)" strokeWidth="0.5" />
            <text x={margin.left - 8} y={y(d) + 4} textAnchor="end" fill="var(--text-muted)"
              fontSize="10" fontFamily="monospace">
              {d % 1 === 0 ? d.toFixed(0) : d.toFixed(1)}
            </text>
          </g>
        ))}
        {/* Curve */}
        <path d={pathD} fill="none" stroke="var(--accent)" strokeWidth="1.5" />
        {/* Axis labels */}
        <text x={margin.left + pw / 2} y={h - 6} textAnchor="middle" fill="var(--text-muted)"
          fontSize="11" fontFamily="monospace">
          {curve.name} {curve.unit ? `(${curve.unit})` : ''}
        </text>
        <text x="12" y={margin.top + ph / 2} textAnchor="middle" fill="var(--text-muted)"
          fontSize="11" fontFamily="monospace"
          transform={`rotate(-90, 12, ${margin.top + ph / 2})`}>
          Depth (m)
        </text>
      </svg>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1>〰 Well Log Viewer</h1>
        <p>Upload a LAS file to view well log curves</p>
      </div>

      <div className="card">
        <div className="upload-zone" onClick={() => inputRef.current?.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]) }}>
          <input ref={inputRef} type="file" accept=".las,.LAS,.txt"
            onChange={e => e.target.files[0] && handleFile(e.target.files[0])} />
          {file ? (
            <div>
              <div style={{ fontSize: 16, color: 'var(--accent)', marginBottom: 4 }}>{file.name}</div>
              <div style={{ fontSize: 12 }}>{(file.size / 1024).toFixed(1)} KB — Click or drop to change</div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: 32, marginBottom: 8 }}>📄</div>
              <div style={{ fontSize: 14 }}>Drop a LAS file here or click to browse</div>
            </div>
          )}
        </div>
      </div>

      {error && <div className="alert error">{error}</div>}

      {parsed && (
        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16 }}>
          <div>
            <div className="card">
              <div className="card-title">Well Info</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                <div>Start: {parsed.header.startDepth?.toFixed(1) ?? '—'} m</div>
                <div>End: {parsed.header.endDepth?.toFixed(1) ?? '—'} m</div>
                <div>Step: {parsed.header.step ?? '—'} m</div>
                <div>Samples: {parsed.asciiData.length}</div>
                <div>Curves: {parsed.curveInfo.length}</div>
              </div>
            </div>
            <div className="card">
              <div className="card-title">Curves ({parsed.curveInfo.length})</div>
              <div className="curve-list" style={{ maxHeight: 400, overflowY: 'auto' }}>
                {parsed.curveInfo.map((c, i) => (
                  <div key={i} className="curve-card"
                    style={{ cursor: 'pointer', border: selectedCurve === i ? '1px solid var(--accent)' : undefined }}
                    onClick={() => setSelectedCurve(i)}>
                    <span className="curve-name">{c.name}</span>
                    <span className="curve-stats">{c.unit} · {c.values.filter(v => v !== null).length} pts</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-title">
              Curve: {selectedCurve !== null ? parsed.curveInfo[selectedCurve]?.name : 'Select a curve'}
            </div>
            {selectedCurve !== null && parsed.curveInfo[selectedCurve] && (
              renderChart(parsed.curveInfo[selectedCurve])
            )}
          </div>
        </div>
      )}
    </div>
  )
}
