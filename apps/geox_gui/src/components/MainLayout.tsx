/**
 * GEOX MainLayout — Seven Dimension Tabs
 * DITEMPA BUKAN DIBERI
 */

import { DimensionId, DIMENSION_LIST, getDimension } from '../types';

interface MainLayoutProps {
  activeDimension: DimensionId;
  onDimensionChange: (dimension: DimensionId) => void;
  children?: React.ReactNode;
}

export function MainLayout({ activeDimension, onDimensionChange, children }: MainLayoutProps) {
  return (
    <div className="geox-main-layout">
      {/* Seven Dimension Tabs */}
      <nav className="dimension-tabs">
        {DIMENSION_LIST.map((dim) => (
          <button
            key={dim.id}
            className={`dimension-tab ${activeDimension === dim.id ? 'active' : ''}`}
            onClick={() => onDimensionChange(dim.id)}
            style={{ '--tab-color': dim.color } as React.CSSProperties}
          >
            <span className="tab-icon">{getTabIcon(dim.icon)}</span>
            <span className="tab-label">{dim.label}</span>
          </button>
        ))}
      </nav>

      {/* Content Area */}
      <main className="dimension-content">
        {children || <DimensionPlaceholder dimension={activeDimension} />}
      </main>
    </div>
  );
}

function DimensionPlaceholder({ dimension }: { dimension: DimensionId }) {
  const dim = getDimension(dimension);
  return (
    <div className="dimension-placeholder" style={{ borderColor: dim.color }}>
      <h2>{dim.label} — {dim.app}</h2>
      <p>{dim.description}</p>
      <p className="seal">DITEMPA BUKAN DIBERI — 999 SEAL</p>
    </div>
  );
}

function getTabIcon(icon: string): string {
  const icons: Record<string, string> = {
    'Globe': '🌐',
    'Database': '🗄️',
    'Layout': '📐',
    'Layers': '🎲',
    'Clock': '⏱️',
    'Zap': '⚡',
    'Map': '🗺️'
  };
  return icons[icon] || '○';
}

export default MainLayout;
