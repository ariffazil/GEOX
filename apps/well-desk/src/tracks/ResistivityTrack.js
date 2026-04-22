/**
 * ResistivityTrack.js — RT / MSFL Track (Logarithmic Scale)
 * ==========================================================
 * Renders resistivity curves on logarithmic scale.
 * Typical range: 0.2–2000 ohm-m (4 decades).
 */

class ResistivityTrack extends TrackBase {
  constructor(config = {}) {
    super("RT", config.color || "#ff4444");
    this.config = {
      min: config.min || 0.2,
      max: config.max || 2000,
      scaleType: "log",
      decades: config.decades || 4,
      ...config
    };
  }

  render(trackGroup, layout) {
    const { width, height, depthTop, depthBase, depthRange } = layout;
    const { min, max } = this.config;
    const { depth, values } = this.data;

    if (!depth.length || depth.length !== values.length) return;

    const logMin = Math.log10(min);
    const logMax = Math.log10(max);

    // Build polyline
    let points = "";
    for (let i = 0; i < depth.length; i++) {
      const frac = (depth[i] - depthTop) / depthRange;
      const y = frac * height;
      const valClamped = Math.max(min, Math.min(max, values[i]));
      const valNorm = (Math.log10(valClamped) - logMin) / (logMax - logMin);
      const x = valNorm * width;

      points += i === 0 ? `${x},${y}` : ` ${x},${y}`;
    }

    // Curve
    const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    polyline.setAttribute("points", points);
    polyline.setAttribute("fill", "none");
    polyline.setAttribute("stroke", this.color);
    polyline.setAttribute("stroke-width", 1.5);
    trackGroup.appendChild(polyline);

    // Scale
    this._renderScale(trackGroup, layout);
  }

  _renderScale(trackGroup, layout) {
    const { width, height } = layout;
    const { min, max, decades } = this.config;

    // Log ticks per decade
    const logMin = Math.log10(min);
    for (let d = 0; d <= decades; d++) {
      const val = min * Math.pow(10, d);
      const frac = d / decades;
      const x = frac * width;

      // Major tick
      const tick = document.createElementNS("http://www.w3.org/2000/svg", "line");
      tick.setAttribute("x1", x);
      tick.setAttribute("y1", height);
      tick.setAttribute("x2", x);
      tick.setAttribute("y2", height + 6);
      tick.setAttribute("stroke", "#666");
      trackGroup.appendChild(tick);

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", x);
      label.setAttribute("y", height + 16);
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("fill", "#888");
      label.setAttribute("font-size", "9px");
      label.textContent = val.toExponential(0).replace("e+", "E");
      trackGroup.appendChild(label);

      // Minor ticks (2, 3, 4, 5, 6, 7, 8, 9)
      for (let m = 2; m <= 9; m++) {
        const minorVal = val * m;
        if (minorVal > max) break;
        const minorLog = Math.log10(minorVal);
        const minorFrac = (minorLog - logMin) / (Math.log10(max) - logMin);
        const minorX = minorFrac * width;

        const minorTick = document.createElementNS("http://www.w3.org/2000/svg", "line");
        minorTick.setAttribute("x1", minorX);
        minorTick.setAttribute("y1", height);
        minorTick.setAttribute("x2", minorX);
        minorTick.setAttribute("y2", height + 3);
        minorTick.setAttribute("stroke", "#444");
        trackGroup.appendChild(minorTick);
      }
    }

    // Unit
    const unit = document.createElementNS("http://www.w3.org/2000/svg", "text");
    unit.setAttribute("x", width - 5);
    unit.setAttribute("y", height + 14);
    unit.setAttribute("text-anchor", "end");
    unit.setAttribute("fill", "#666");
    unit.setAttribute("font-size", "9px");
    unit.textContent = "ohm-m";
    trackGroup.appendChild(unit);
  }
}
