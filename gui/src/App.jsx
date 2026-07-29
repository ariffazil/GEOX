import { Routes, Route, NavLink } from 'react-router-dom'
import ToolCatalog from './pages/ToolCatalog.jsx'
import CrossSectionBuilder from './pages/CrossSectionBuilder.jsx'
import WellLogViewer from './pages/WellLogViewer.jsx'

function App() {
  return (
    <div className="app">
      <nav className="sidebar">
        <div className="sidebar-header">
          <div className="logo">Φ GEOX</div>
          <div className="subtitle">Earth Intelligence</div>
        </div>
        <ul className="nav-links">
          <li>
            <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              <span className="nav-icon">⊞</span>
              Tool Catalog
            </NavLink>
          </li>
          <li>
            <NavLink to="/cross-section" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              <span className="nav-icon">⬡</span>
              Cross-Section Builder
            </NavLink>
          </li>
          <li>
            <NavLink to="/well-log" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              <span className="nav-icon">〰</span>
              Well Log Viewer
            </NavLink>
          </li>
        </ul>
        <div className="sidebar-footer">
          <div className="version">v2026.07.29</div>
          <div className="federation-badge">arifOS Federation</div>
        </div>
      </nav>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<ToolCatalog />} />
          <Route path="/cross-section" element={<CrossSectionBuilder />} />
          <Route path="/well-log" element={<WellLogViewer />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
