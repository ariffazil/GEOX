/**
 * SonicTrack.js — DT (Delta-T) Track (Linear Scale)
 * ==================================================
 * Compressional sonic transit time.
 * Typical range: 40–140 us/ft (sand to shale).
 */

class SonicTrack extends TrackBase {
  constructor(config = {}) {
    super("DT", config.color || "#ffff00");
    this.config = {
      min: config.min || 40,     // us/ft — compact sand
      max: config.max || 140,    // us/ft — shale
      scaleType: "linear",
      ...config
    };
  }

  render(trackGroup, layout) {
    const { width, height, depthTop, depthBase, depthRange } = layout;
    const { min, max } = this.config;
    const { depth, values } = this.data;

    if (!depth.length || depth.length !== values.length) return;

    let points = "";
    for (let i = 0; i < depth.length; i++) {
      const frac = (depth[i] - depthTop) / depthRange;
      const y = frac * height;
      const valNorm = Math.max(0, Math.min(1, (values[i] - min) / (max - min)));
      const x = valNorm * width;

      points += i === 0 ? `${x},${y}` : ` ${x},${y}`;
    }

    // Main curve
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

    const unit = document.createElementNS("http://www.w3.org/2000/svg", "text");
    unit.setAttribute("x", width - 5);
    unit.setAttribute("y", height + 14);
    unit.setAttribute("text-anchor", "end");
    unit.setAttribute("fill", "#666");
    unit.setAttribute("font-size", "9px");
    unit.textContent = "us/ft";
    trackGroup.appendChild(unit);
  }
}
