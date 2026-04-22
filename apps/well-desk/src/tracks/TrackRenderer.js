/**
 * TrackRenderer.js — SVG Depth-Indexed Track Renderer
 * =====================================================
 * Base renderer for all well log tracks. Handles shared depth axis,
 * zoom, hover tooltips, and track layout.
 *
 * fsh-linux naming. Scientific geology only.
 */

class TrackRenderer {
  constructor(containerId, config = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) throw new Error(`TrackRenderer: container #${containerId} not found`);

    this.config = {
      trackWidth: 180,
      trackHeight: 800,
      depthTop: config.depthTop || 3000,
      depthBase: config.depthBase || 4000,
      pixelsPerMeter: config.pixelsPerMeter || 2,
      marginLeft: 40,
      marginRight: 10,
      marginTop: 20,
      marginBottom: 20,
      ...config
    };

    this.depthRange = this.config.depthBase - this.config.depthTop;
    this.tracks = [];       // Registered track instances
    this.svg = null;        // Root SVG element
    this.depthAxis = null;  // Shared depth axis group
    this.trackGroups = [];  // Per-track SVG groups

    this._initSvg();
    this._initDepthAxis();
    this._bindEvents();
  }

  // ── SVG Initialization ────────────────────────────────────────────────────

  _initSvg() {
    const { trackWidth, trackHeight, marginLeft, marginRight } = this.config;
    const totalWidth = marginLeft + (this.tracks.length * trackWidth) + marginRight;

    this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    this.svg.setAttribute("width", "100%");
    this.svg.setAttribute("height", `${trackHeight}px`);
    this.svg.setAttribute("viewBox", `0 0 ${totalWidth} ${trackHeight}`);
    this.svg.style.fontFamily = "monospace";
    this.svg.style.fontSize = "10px";
    this.container.appendChild(this.svg);

    // Background
    const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bg.setAttribute("width", totalWidth);
    bg.setAttribute("height", trackHeight);
    bg.setAttribute("fill", "#0f0f1a");
    this.svg.appendChild(bg);
  }

  _initDepthAxis() {
    const { marginLeft, marginTop, marginBottom, trackHeight, depthTop, depthBase } = this.config;
    const plotHeight = trackHeight - marginTop - marginBottom;

    this.depthAxis = document.createElementNS("http://www.w3.org/2000/svg", "g");
    this.depthAxis.setAttribute("transform", `translate(${marginLeft}, ${marginTop})`);
    this.svg.appendChild(this.depthAxis);

    // Depth axis line
    const axisLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    axisLine.setAttribute("x1", 0);
    axisLine.setAttribute("y1", 0);
    axisLine.setAttribute("x2", 0);
    axisLine.setAttribute("y2", plotHeight);
    axisLine.setAttribute("stroke", "#888");
    axisLine.setAttribute("stroke-width", 1);
    this.depthAxis.appendChild(axisLine);

    // Tick marks and labels
    const tickCount = 10;
    for (let i = 0; i <= tickCount; i++) {
      const frac = i / tickCount;
      const depthVal = depthTop + frac * (depthBase - depthTop);
      const y = frac * plotHeight;

      // Tick
      const tick = document.createElementNS("http://www.w3.org/2000/svg", "line");
      tick.setAttribute("x1", -5);
      tick.setAttribute("y1", y);
      tick.setAttribute("x2", 0);
      tick.setAttribute("y2", y);
      tick.setAttribute("stroke", "#888");
      tick.setAttribute("stroke-width", 1);
      this.depthAxis.appendChild(tick);

      // Label
      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", -8);
      label.setAttribute("y", y + 3);
      label.setAttribute("text-anchor", "end");
      label.setAttribute("fill", "#ccc");
      label.textContent = Math.round(depthVal).toString();
      this.depthAxis.appendChild(label);

      // Grid line across all tracks
      if (i > 0 && i < tickCount) {
        const gridLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
        gridLine.setAttribute("x1", 0);
        gridLine.setAttribute("y1", y);
        gridLine.setAttribute("x2", "100%");
        gridLine.setAttribute("y2", y);
        gridLine.setAttribute("stroke", "#333");
        gridLine.setAttribute("stroke-dasharray", "2,4");
        gridLine.setAttribute("opacity", 0.5);
        this.depthAxis.appendChild(gridLine);
      }
    }

    // Depth label
    const depthLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    depthLabel.setAttribute("x", -30);
    depthLabel.setAttribute("y", plotHeight / 2);
    depthLabel.setAttribute("text-anchor", "middle");
    depthLabel.setAttribute("fill", "#aaa");
    depthLabel.setAttribute("transform", `rotate(-90, -30, ${plotHeight / 2})`);
    depthLabel.textContent = "DEPTH (m)";
    this.depthAxis.appendChild(depthLabel);
  }

  // ── Track Registration ────────────────────────────────────────────────────

  addTrack(trackInstance) {
    const trackIndex = this.tracks.length;
    this.tracks.push(trackInstance);

    // Create track group
    const { marginLeft, trackWidth, marginTop, trackHeight, marginBottom } = this.config;
    const plotHeight = trackHeight - marginTop - marginBottom;
    const xOffset = marginLeft + trackIndex * trackWidth;

    const trackGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    trackGroup.setAttribute("transform", `translate(${xOffset}, ${marginTop})`);
    trackGroup.setAttribute("class", `track-${trackIndex}`);
    this.svg.appendChild(trackGroup);
    this.trackGroups.push(trackGroup);

    // Track border
    const border = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    border.setAttribute("width", trackWidth);
    border.setAttribute("height", plotHeight);
    border.setAttribute("fill", "none");
    border.setAttribute("stroke", "#444");
    border.setAttribute("stroke-width", 1);
    trackGroup.appendChild(border);

    // Track header
    const header = document.createElementNS("http://www.w3.org/2000/svg", "text");
    header.setAttribute("x", trackWidth / 2);
    header.setAttribute("y", -6);
    header.setAttribute("text-anchor", "middle");
    header.setAttribute("fill", trackInstance.color || "#fff");
    header.setAttribute("font-weight", "bold");
    header.setAttribute("font-size", "11px");
    header.textContent = trackInstance.name || `Track ${trackIndex}`;
    trackGroup.appendChild(header);

    // Render track content
    trackInstance.render(trackGroup, {
      width: trackWidth,
      height: plotHeight,
      depthTop: this.config.depthTop,
      depthBase: this.config.depthBase,
      depthRange: this.depthRange
    });

    // Update SVG viewBox
    const totalWidth = marginLeft + (this.tracks.length * trackWidth) + this.config.marginRight;
    this.svg.setAttribute("viewBox", `0 0 ${totalWidth} ${trackHeight}`);

    return trackIndex;
  }

  // ── Zoom ──────────────────────────────────────────────────────────────────

  setDepthRange(topM, baseM) {
    this.config.depthTop = topM;
    this.config.depthBase = baseM;
    this.depthRange = baseM - topM;
    this.refresh();
  }

  refresh() {
    // Clear and redraw
    this.svg.innerHTML = "";
    this.trackGroups = [];
    this._initDepthAxis();
    // Re-render tracks
    const existingTracks = [...this.tracks];
    this.tracks = [];
    existingTracks.forEach(t => this.addTrack(t));
  }

  // ── Hover Tooltip ─────────────────────────────────────────────────────────

  _bindEvents() {
    const tooltip = document.createElement("div");
    tooltip.className = "track-tooltip";
    tooltip.style.cssText = `
      position: absolute; background: rgba(0,0,0,0.85); color: #0f0;
      padding: 4px 8px; border-radius: 4px; font-family: monospace;
      font-size: 11px; pointer-events: none; display: none; z-index: 100;
      border: 1px solid #0f0;
    `;
    this.container.style.position = "relative";
    this.container.appendChild(tooltip);

    this.svg.addEventListener("mousemove", (e) => {
      const rect = this.svg.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const { marginLeft, marginTop, trackHeight, marginBottom, depthTop, depthBase } = this.config;
      const plotHeight = trackHeight - marginTop - marginBottom;

      if (y >= marginTop && y <= marginTop + plotHeight && x >= marginLeft) {
        const frac = (y - marginTop) / plotHeight;
        const depthVal = depthTop + frac * (depthBase - depthTop);

        // Find which track
        const trackIndex = Math.floor((x - marginLeft) / this.config.trackWidth);

        tooltip.style.display = "block";
        tooltip.style.left = `${e.clientX - rect.left + 12}px`;
        tooltip.style.top = `${e.clientY - rect.top - 10}px`;

        let valueStr = "";
        if (trackIndex >= 0 && trackIndex < this.tracks.length) {
          const track = this.tracks[trackIndex];
          const val = track.getValueAtDepth(depthVal);
          valueStr = val !== null ? `<br>${track.name}: ${val.toFixed(2)}` : "";
        }

        tooltip.innerHTML = `Depth: ${depthVal.toFixed(1)} m${valueStr}`;
      } else {
        tooltip.style.display = "none";
      }
    });

    this.svg.addEventListener("mouseleave", () => {
      tooltip.style.display = "none";
    });
  }

  // ── Export ────────────────────────────────────────────────────────────────

  exportSvg() {
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(this.svg);
    const blob = new Blob([svgStr], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `well-desk-${Date.now()}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

// Base class for individual tracks
class TrackBase {
  constructor(name, color = "#0f0") {
    this.name = name;
    this.color = color;
    this.data = { depth: [], values: [] };
    this.config = { min: 0, max: 100, scaleType: "linear" };
  }

  setData(depthArray, valueArray) {
    this.data.depth = depthArray;
    this.data.values = valueArray;
  }

  getValueAtDepth(targetDepth) {
    const { depth, values } = this.data;
    if (!depth.length) return null;
    // Linear interpolation
    for (let i = 0; i < depth.length - 1; i++) {
      if ((depth[i] <= targetDepth && depth[i + 1] >= targetDepth) ||
          (depth[i] >= targetDepth && depth[i + 1] <= targetDepth)) {
        const t = (targetDepth - depth[i]) / (depth[i + 1] - depth[i]);
        return values[i] + t * (values[i + 1] - values[i]);
      }
    }
    return null;
  }

  _scaleValue(value, layout) {
    const { min, max, scaleType } = this.config;
    if (scaleType === "log") {
      const logMin = Math.log10(Math.max(min, 0.1));
      const logMax = Math.log10(Math.max(max, 0.1));
      const logVal = Math.log10(Math.max(value, 0.1));
      return (logVal - logMin) / (logMax - logMin);
    }
    return (value - min) / (max - min);
  }

  render(trackGroup, layout) {
    throw new Error("TrackBase.render() must be implemented by subclass");
  }
}
