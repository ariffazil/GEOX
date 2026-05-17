import React from 'react';

/**
 * GEOX App X-2D: THE GEOMETRY
 * Domain: Planar Subsurface Intelligence
 * Substrates: Strata, Break, Elastic
 */
export const X2D_Shell: React.FC = () => {
    return (
        <div className="flex flex-col h-full bg-geox-black text-slate-100 font-outfit overflow-hidden">
            <header className="h-12 glass border-b flex items-center px-6">
                <h2 className="text-sm font-semibold tracking-widest uppercase">
                    X-2D <span className="text-purple-400">GEOMETRY</span>
                </h2>
            </header>
            
            <main className="flex-1 flex p-4 gap-4 overflow-hidden">
                <aside className="w-64 glass rounded-xl p-4 flex flex-col gap-4">
                    <div className="text-[10px] uppercase tracking-widest text-slate-500">Substrates</div>
                    <div className="flex flex-col gap-2">
                        <button className="substrate-card">Strata (Time)</button>
                        <button className="substrate-card active">Breaks (Tectonic)</button>
                        <button className="substrate-card">Elastic (Wave)</button>
                    </div>
                </aside>

                <section className="flex-1 glass rounded-xl relative flex items-center justify-center border-dashed border-white/10">
                    {/* Placeholder for Seismic Canvas / Section Viewer */}
                    <div className="text-center">
                        <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-purple-500/30">
                            <i className="geox-icon-planar"></i>
                        </div>
                        <p className="text-sm opacity-50 font-light">Load canonical Break evidence to visualize tectonic displacement.</p>
                    </div>
                </section>
            </main>
        </div>
    );
};
