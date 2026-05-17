import React from 'react';

/**
 * GEOX App X-3D: THE STATE
 * Domain: Volumetric & Dynamic Subsurface Intelligence
 * Substrates: Kinetic, Stress, Flow
 */
export const X3D_Shell: React.FC = () => {
    return (
        <div className="flex flex-col h-full bg-geox-black text-slate-100 font-outfit overflow-hidden">
            <header className="h-12 glass border-b flex items-center px-6">
                <h2 className="text-sm font-semibold tracking-widest uppercase">
                    X-3D <span className="text-amber-400">STATE</span>
                </h2>
            </header>
            
            <main className="flex-1 flex p-4 gap-4 overflow-hidden">
                <aside className="w-64 glass rounded-xl p-4 flex flex-col gap-4">
                    <div className="text-[10px] uppercase tracking-widest text-slate-500">Substrates</div>
                    <div className="flex flex-col gap-2">
                        <button className="substrate-card">Kinetic (Energy)</button>
                        <button className="substrate-card active">Stress (Pressure)</button>
                        <button className="substrate-card">Flow (Flux)</button>
                    </div>
                </aside>

                <section className="flex-1 glass rounded-xl relative flex items-center justify-center border-dashed border-white/10">
                    {/* Placeholder for Volumetric Renderer */}
                    <div className="text-center">
                        <div className="w-16 h-16 bg-amber-500/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-amber-500/30">
                            <i className="geox-icon-volumetric"></i>
                        </div>
                        <p className="text-sm opacity-50 font-light">Load canonical Stress evidence to analyze geomechanical stability.</p>
                    </div>
                </section>
            </main>
        </div>
    );
};
