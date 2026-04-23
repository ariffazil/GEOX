/**
 * GEOX App Shells — 3 Apps / 9 Substrates
 * DITEMPA BUKAN DIBERI
 */

export type AppId = 'x1d' | 'x2d' | 'x3d' | 'arifos';

export type SubstrateId = 
  | 'lithos' | 'pore' | 'fluid'    // X-1D
  | 'strata' | 'break' | 'elastic'  // X-2D
  | 'kinetic' | 'stress' | 'flow';  // X-3D

export interface Substrate {
  id: SubstrateId;
  app: AppId;
  label: string;
  physics_hook: string;
  description: string;
  unit: string;
}

export const SUBSTRATES: Record<SubstrateId, Substrate> = {
  // X-1D: Material
  lithos: { id: 'lithos', app: 'x1d', label: 'Lithos', physics_hook: 'Mass', description: 'Rock fabric & density', unit: 'rho_b' },
  pore: { id: 'pore', app: 'x1d', label: 'Pores', physics_hook: 'Volume', description: 'Void space & permeability', unit: 'phi' },
  fluid: { id: 'fluid', app: 'x1d', label: 'Fluids', physics_hook: 'Saturation', description: 'Saturation & fluid type', unit: 'Sw' },
  
  // X-2D: Geometry
  strata: { id: 'strata', app: 'x2d', label: 'Strata', physics_hook: 'Time', description: 'Stacking & sequence', unit: 't' },
  break: { id: 'break', app: 'x2d', label: 'Breaks', physics_hook: 'Displacement', description: 'Faults & fractures', unit: 'u' },
  elastic: { id: 'elastic', app: 'x2d', label: 'Elastic', physics_hook: 'Velocity', description: 'Impedance & waves', unit: 'V' },
  
  // X-3D: State
  kinetic: { id: 'kinetic', app: 'x3d', label: 'Kinetic', physics_hook: 'Energy', description: 'Maturity & heat', unit: 'T' },
  stress: { id: 'stress', app: 'x3d', label: 'Stress', physics_hook: 'Pressure', description: 'Pressure & stability', unit: 'P' },
  flow: { id: 'flow', app: 'x3d', label: 'Flow', physics_hook: 'Flux', description: 'Dynamics & flux', unit: 'k' },
};