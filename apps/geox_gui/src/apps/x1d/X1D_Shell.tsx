import React from 'react';

/**
 * GEOX App X-1D: THE MATERIAL
 * Domain: Vertical Subsurface Intelligence
 * Substrates: Lithos, Pore, Fluid
 */
export const X1D_Shell: React.FC = () => {
    return (
        <div className="flex flex-col h-full bg-geox-black text-slate-100 font-outfit overflow-hidden">
            <header className="h-12 glass border-b flex items-center px-6">
                <h2 className="text-sm font-semibold tracking-widest uppercase">
                    X-1D <span className="text-blue-400">MATERIAL</span>
                </h2>
            </header>
            
            <main className="flex-1 flex p-4 gap-4 overflow-hidden">
                {/* Lateral Navigation - Substrate Selector */}
                <aside className="w-64 glass rounded-xl p-4 flex flex-col gap-4">
                    <div className="text-[10px] uppercase tracking-widest text-slate-500">Substrates</div>
                    <div className="flex flex-col gap-2">
                        <button className="substrate-card active">Lithos (Matrix)</button>
                        <button className="substrate-card">Pores (Void)</button>
                        <button className="substrate-card">Fluids (Charge)</button>
                    </div>
                </aside>

                {/* Main Workspace */}
                <section className="flex-1 glass rounded-xl relative flex items-center justify-center border-dashed border-white/10">
                    <div className="text-center">
                        <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-blue-500/30">
                            <i className="geox-icon-vertical"></i>
                        </div>
                        <p className="text-sm opacity-50 font-light">Load canonical Lithos evidence to begin vertical evaluation.</p>
                    </div>
                </section>
            </main>
        </div>
    );
};
