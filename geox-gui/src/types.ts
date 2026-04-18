/**
 * GEOX Tab Types — Seven Dimensions
 * DITEMPA BUKAN DIBERI
 */

export type DimensionId = 
  | 'prospect' 
  | 'well' 
  | 'section' 
  | 'earth3d' 
  | 'time4d' 
  | 'physics' 
  | 'map';

export interface Dimension {
  id: DimensionId;
  label: string;
  icon: string;
  color: string;
  description: string;
  app: string;
}

export const DIMENSIONS: Record<DimensionId, Dimension> = {
  prospect: {
    id: 'prospect',
    label: 'Prospect',
    icon: 'Globe',
    color: '#3b82f6',
    description: 'Play fairway discovery & ToAC scaling',
    app: 'ProspectExplore'
  },
  well: {
    id: 'well',
    label: 'Well',
    icon: 'Database',
    color: '#22c55e',
    description: 'Truth Witness: Borehole & log analysis',
    app: 'WellContext'
  },
  section: {
    id: 'section',
    label: 'Section',
    icon: 'Layout',
    color: '#a855f7',
    description: 'Stratigraphic continuity & 2D correlation',
    app: 'SectionView'
  },
  earth3d: {
    id: 'earth3d',
    label: 'Earth 3D',
    icon: 'Layers',
    color: '#f59e0b',
    description: 'Volumetric synthesis & seismic interpretation',
    app: 'Earth3D'
  },
  time4d: {
    id: 'time4d',
    label: 'Time 4D',
    icon: 'Clock',
    color: '#ef4444',
    description: 'Basin evolution & play cycle timing',
    app: 'Time4D'
  },
  physics: {
    id: 'physics',
    label: 'Physics',
    icon: 'Zap',
    color: '#ec4899',
    description: '888_JUDGE governance & state verification',
    app: 'PhysicsConsole'
  },
  map: {
    id: 'map',
    label: 'Map',
    icon: 'Map',
    color: '#06b6d4',
    description: 'Transversal spatial fabric (Malay Basin Pilot)',
    app: 'MapRegistry'
  }
};

export const DIMENSION_LIST = Object.values(DIMENSIONS);

export function getDimension(id: DimensionId): Dimension {
  return DIMENSIONS[id];
}