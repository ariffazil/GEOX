/**
 * GRTrack.js — Gamma Ray Track (Linear Scale, Shale Fill)
 * ========================================================
 * Renders GR curve with linear scale and optional shale volume fill.
 * GR ranges: 0–150 API (clean to shale baseline).
 */

class GRTrack extends TrackBase {
  constructor(config = {}) {
    super("GR", config.color || "#00ff88");
    this.config = {
      min: config.min || 0,
      max: config.max || 150,
      scaleType: "linear",
      shaleFillColor: config.shaleFillColor || "rgba(255, 165, 0, 0.3)",
      sandLineColor: config.sandLineColor || "#00ff88",
      shaleBaseline: config.shaleBaseline || 100,  // API units
      ...config
    };
  }

  render(trackGroup, layout) {
    const { width, height, depthTop, depthBase, depthRange } = layout;
    const { min, max, shaleBaseline } = this.config;
    const { depth, values } = this.data;

    if (!depth.length || depth.length !== values.length) return;

    // Sand baseline at min GR (clean sand)
    const sandY = height;  // Bottom = low GR (sand)
    const baselineFrac = (shaleBaseline - min) / (max - min);
    const baselineY = height * (1 - baselineFrac);

    // Build polyline points
    let points = "";
    let fillPoints = `0,${height} `; // Start bottom-left

    for (let i = 0; i < depth.length; i++) {
      const frac = (depth[i] - depthTop) / depthRange;
      const y = frac * height;
      const valNorm = Math.max(0, Math.min(1, (values[i] - min) / (max - min)));
      const x = valNorm * width;

      if (i === 0) {
        points += `${x},${y}`;
        fillPoints += `${x},${y} `;
      } else {
        points += ` ${x},${y}`;
        fillPoints += `${x},${y} `;
      }
    }

    // Fill area above shale baseline (shale indicator)
    const fillPoly = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    fillPoly.setAttribute("points", fillPoints + `${width},${height}`);
    fillPoly.setAttribute("fill", this.config.shaleFillColor);
    trackGroup.appendChild(fillPoly);

    // GR curve line
    const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    polyline.setAttribute("points", points);
    polyline.setAttribute("fill", "none");
    polyline.setAttribute("stroke", this.color);
    polyline.setAttribute("stroke-width", 1.5);
    polyline.setAttribute("stroke-linecap", "round");
    polyline.setAttribute("stroke-linejoin", "round");
    trackGroup.appendChild(polyline);

    // Scale ticks
    this._renderScale(trackGroup, layout);
  }

  _renderScale(trackGroup, layout) {
    const { width, height } = layout;
    const { min, max } = this.config;
    const tickCount = 5;

    for (let i = 0; i <= tickCount; i++) {
      const frac = i / tickCount;
      const val = min + frac * (max - min);
      const x = frac * width;

      const tick = document.createElementNS("http://www.w3.org/2000/svg", "line");
      tick.setAttribute("x1", x);
      tick.setAttribute("y1", height);
      tick.setAttribute("x2", x);
      tick.setAttribute("y2", height + 5);
      tick.setAttribute("stroke", "#666");
      trackGroup.appendChild(tick);

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", x);
      label.setAttribute("y", height + 14);
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("fill", "#888");
      label.setAttribute("font-size", "9px");
      label.textContent = Math.round(val).toString();
      trackGroup.appendChild(label);
    }

    // Unit label
    const unit = document.createElementNS("http://www.w3.org/2000/svg", "text");
    unit.setAttribute("x", width - 5);
    unit.setAttribute("y", height + 14);
    unit.setAttribute("text-anchor", "end");
    unit.setAttribute("fill", "#666");
    unit.setAttribute("font-size", "9px");
    unit.textContent = "API";
    trackGroup.appendChild(unit);
  }
}
