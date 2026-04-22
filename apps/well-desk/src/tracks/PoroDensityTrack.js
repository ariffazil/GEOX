/**
 * PoroDensityTrack.js — NPHI + RHOB Overlay (Crossover Fill)
 * ===========================================================
 * Dual-curve track with gas crossover detection.
 * NPHI (0–0.45 v/v) and RHOB (1.95–2.95 g/cm3) on shared depth axis.
 * Crossover fill indicates gas-bearing zones.
 */

class PoroDensityTrack extends TrackBase {
  constructor(config = {}) {
    super("NPHI-RHOB", config.color || "#ff00ff");
    this.config = {
      nphiMin: config.nphiMin || 0.0,
      nphiMax: config.nphiMax || 0.45,
      rhobMin: config.rhobMin || 1.95,
      rhobMax: config.rhobMax || 2.95,
      crossoverFill: config.crossoverFill || "rgba(255, 255, 0, 0.4)",  // Gas = yellow
      ...config
    };
    this.nphiData = { depth: [], values: [] };
    this.rhobData = { depth: [], values: [] };
  }

  setNPHI(depthArray, valueArray) {
    this.nphiData.depth = depthArray;
    this.nphiData.values = valueArray;
  }

  setRHOB(depthArray, valueArray) {
    this.rhobData.depth = depthArray;
    this.rhobData.values = valueArray;
  }

  render(trackGroup, layout) {
    const { width, height, depthTop, depthBase, depthRange } = layout;
    const { nphiMin, nphiMax, rhobMin, rhobMax, crossoverFill } = this.config;

    // Render NPHI curve
    this._renderCurve(trackGroup, layout, this.nphiData, nphiMin, nphiMax, "#ff00ff", "solid");

    // Render RHOB curve
    this._renderCurve(trackGroup, layout, this.rhobData, rhobMin, rhobMax, "#00ffff", "solid");

    // Gas crossover fill
    this._renderCrossover(trackGroup, layout);

    // Dual scale
    this._renderDualScale(trackGroup, layout);
  }

  _renderCurve(trackGroup, layout, data, min, max, color, style) {
    const { width, height, depthTop, depthRange } = layout;
    const { depth, values } = data;
    if (!depth.length || depth.length !== values.length) return;

    let points = "";
    for (let i = 0; i < depth.length; i++) {
      const frac = (depth[i] - depthTop) / depthRange;
      const y = frac * layout.height;
      const valNorm = Math.max(0, Math.min(1, (values[i] - min) / (max - min)));
      const x = valNorm * width;
      points += i === 0 ? `${x},${y}` : ` ${x},${y}`;
    }

    const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    polyline.setAttribute("points", points);
    polyline.setAttribute("fill", "none");
    polyline.setAttribute("stroke", color);
    polyline.setAttribute("stroke-width", 1.5);
    if (style === "dashed") {
      polyline.setAttribute("stroke-dasharray", "4,3");
    }
    trackGroup.appendChild(polyline);
  }

  _renderCrossover(trackGroup, layout) {
    const { width, height, depthTop, depthRange } = layout;
    const { nphiMin, nphiMax, rhobMin, rhobMax, crossoverFill } = this.config;
    const { depth: dN, values: vN } = this.nphiData;
    const { depth: dR, values: vR } = this.rhobData;

    if (!dN.length || !dR.length) return;

    // Build crossover polygons where NPHI > RHOB (gas indicator)
    // Normalize both to 0-1 for comparison
    let inCrossover = false;
    let polyPoints = "";

    const step = Math.max(1, Math.floor(dN.length / 500)); // Downsample for performance

    for (let i = 0; i < dN.length; i += step) {
      const frac = (dN[i] - depthTop) / depthRange;
      const y = frac * height;
      const nphiNorm = (vN[i] - nphiMin) / (nphiMax - nphiMin);

      // Interpolate RHOB at this depth
      let rhobVal = this._interpolate(dR, vR, dN[i]);
      if (rhobVal === null) continue;
      const rhobNorm = (rhobVal - rhobMin) / (rhobMax - rhobMin);

      const isCrossover = nphiNorm > rhobNorm;

      if (isCrossover && !inCrossover) {
        inCrossover = true;
        polyPoints = `${nphiNorm * width},${y} `;
      } else if (isCrossover && inCrossover) {
        polyPoints += `${nphiNorm * width},${y} ${rhobNorm * width},${y} `;
      } else if (!isCrossover && inCrossover) {
        inCrossover = false;
        if (polyPoints) {
          const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
          polygon.setAttribute("points", polyPoints.trim());
          polygon.setAttribute("fill", crossoverFill);
          trackGroup.appendChild(polygon);
          polyPoints = "";
        }
      }
    }
  }

  _interpolate(depthArr, valArr, targetDepth) {
    for (let i = 0; i < depthArr.length - 1; i++) {
      if ((depthArr[i] <= targetDepth && depthArr[i + 1] >= targetDepth) ||
          (depthArr[i] >= targetDepth && depthArr[i + 1] <= targetDepth)) {
        const t = (targetDepth - depthArr[i]) / (depthArr[i + 1] - depthArr[i]);
        return valArr[i] + t * (valArr[i + 1] - valArr[i]);
      }
    }
    return null;
  }

  _renderDualScale(trackGroup, layout) {
    const { width, height } = layout;
    const { nphiMin, nphiMax, rhobMin, rhobMax } = this.config;

    // Left scale: NPHI
    for (let i = 0; i <= 4; i++) {
      const frac = i / 4;
      const val = nphiMin + frac * (nphiMax - nphiMin);
      const x = frac * width;

      const tick = document.createElementNS("http://www.w3.org/2000/svg", "line");
      tick.setAttribute("x1", x);
      tick.setAttribute("y1", 0);
      tick.setAttribute("x2", x);
      tick.setAttribute("y2", -5);
      tick.setAttribute("stroke", "#f0f");
      trackGroup.appendChild(tick);

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", x);
      label.setAttribute("y", -8);
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("fill", "#f0f");
      label.setAttribute("font-size", "9px");
      label.textContent = val.toFixed(2);
      trackGroup.appendChild(label);
    }

    // Right scale: RHOB
    for (let i = 0; i <= 4; i++) {
      const frac = i / 4;
      const val = rhobMin + frac * (rhobMax - rhobMin);
      const x = frac * width;

      const tick = document.createElementNS("http://www.w3.org/2000/svg", "line");
      tick.setAttribute("x1", x);
      tick.setAttribute("y1", height);
      tick.setAttribute("x2", x);
      tick.setAttribute("y2", height + 5);
      tick.setAttribute("stroke", "#0ff");
      trackGroup.appendChild(tick);

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", x);
      label.setAttribute("y", height + 14);
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("fill", "#0ff");
      label.setAttribute("font-size", "9px");
      label.textContent = val.toFixed(2);
      trackGroup.appendChild(label);
    }

    // Unit labels
    const nphiUnit = document.createElementNS("http://www.w3.org/2000/svg", "text");
    nphiUnit.setAttribute("x", 5);
    nphiUnit.setAttribute("y", -8);
    nphiUnit.setAttribute("fill", "#f0f");
    nphiUnit.setAttribute("font-size", "9px");
    nphiUnit.textContent = "NPHI";
    trackGroup.appendChild(nphiUnit);

    const rhobUnit = document.createElementNS("http://www.w3.org/2000/svg", "text");
    rhobUnit.setAttribute("x", width - 5);
    rhobUnit.setAttribute("y", height + 14);
    rhobUnit.setAttribute("text-anchor", "end");
    rhobUnit.setAttribute("fill", "#0ff");
    rhobUnit.setAttribute("font-size", "9px");
    rhobUnit.textContent = "RHOB g/cm3";
    trackGroup.appendChild(rhobUnit);
  }
}
