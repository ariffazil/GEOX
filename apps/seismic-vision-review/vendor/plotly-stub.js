/* GEOX Seismic Vendor — minimal Plotly stub (no external CDN).
   For production, replace with pinned plotly-2.35.2.min.js.
   This stub keeps the page working when offline. */
window.Plotly = window.Plotly || {
  newPlot: (el, _d, _l, _o) => {
    const node = typeof el === "string" ? document.getElementById(el) : el;
    if (node) node.textContent = "[Plotly stub] install pinned plotly-2.35.2.min.js for production rendering.";
  },
  react: () => {},
  purge: () => {},
  relayout: () => {},
};