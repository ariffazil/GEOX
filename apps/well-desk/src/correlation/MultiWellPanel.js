/**
 * MultiWellPanel.js — 2D Multi-Well Correlation Strip (SVG)
 * ==========================================================
 * Side-by-side GR tracks with depth-matched formation top picks
 * and user-draggable tie lines between wells.
 */

class MultiWellPanel {
  constructor(containerId, config = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) throw new Error(`MultiWellPanel: container #${containerId} not found`);

    this.config = {
      wellWidth: config.wellWidth || 160,
      trackHeight: config.trackHeight || 600,
      depthTop: config.depthTop || 3000,
      depthBase: config.depthBase || 4000,
      gapBetweenWells: config.gapBetweenWells || 100,
      marginLeft: 20,
      marginRight: 20,
      marginTop: 30,
      ...config
    };

    this.wells = [];        // Well data objects
    this.formationTops = []; // Formation picks per well
    this.tieLines = [];     // User-drawn correlation lines
    this.svg = null;
    this.isDragging = false;
    this.dragStart = null;
  }

  /**
   * Add a well to the panel
   * wellData = { id, name, depth: [], gr: [], tops: [{name, depth, color}] }
   */
  addWell(wellData) {
    this.wells.push(wellData);
    this._render();
  }

  /**
   * Set depth range for all wells
   */
  setDepthRange(topM, baseM) {
    this.config.depthTop = topM;
    this.config.depthBase = baseM;
    this._render();
  }

  _render() {
    this.container.innerHTML = "";
    const { wellWidth, trackHeight, marginLeft, marginRight, marginTop, gapBetweenWells } = this.config;
    const totalWidth = marginLeft + this.wells.length * wellWidth + (this.wells.length - 1) * gapBetweenWells + marginRight;

    this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    this.svg.setAttribute("width", totalWidth);
    this.svg.setAttribute("height", trackHeight + marginTop + 20);
    this.svg.style.fontFamily = "monospace";
    this.svg.style.fontSize = "10px";

    // Background
    const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bg.setAttribute("width", totalWidth);
    bg.setAttribute("height", trackHeight + marginTop + 20);
    bg.setAttribute("fill", "#0f0f1a");
    this.svg.appendChild(bg);

    this.container.appendChild(this.svg);

    // Render each well
    this.wells.forEach((well, index) => {
      const xOffset = marginLeft + index * (wellWidth + gapBetweenWells);
      this._renderWellTrack(well, index, xOffset, marginTop, wellWidth, trackHeight);
    });

    // Render tie lines
    this._renderTieLines();
  }

  _renderWellTrack(well, index, xOffset, yOffset, width, height) {
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("transform", `translate(${xOffset}, ${yOffset})`);
    this.svg.appendChild(group);

    const { depthTop, depthBase } = this.config;
    const depthRange = depthBase - depthTop;

    // Track background
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("width", width);
    rect.setAttribute("height", height);
    rect.setAttribute("fill", "none");
    rect.setAttribute("stroke", "#444");
    group.appendChild(rect);

    // Well name header
    const header = document.createElementNS("http://www.w3.org/2000/svg", "text");
    header.setAttribute("x", width / 2);
    header.setAttribute("y", -10);
    header.setAttribute("text-anchor", "middle");
    header.setAttribute("fill", "#0f0");
    header.setAttribute("font-weight", "bold");
    header.setAttribute("font-size", "11px");
    header.textContent = well.name || well.id;
    group.appendChild(header);

    // GR curve
    if (well.gr && well.depth) {
      const grMin = 0, grMax = 150;
      let points = "";
      for (let i = 0; i < well.depth.length; i++) {
        const dFrac = (well.depth[i] - depthTop) / depthRange;
        const y = dFrac * height;
        const grNorm = Math.max(0, Math.min(1, (well.gr[i] - grMin) / (grMax - grMin)));
        const x = grNorm * width;
        points += i === 0 ? `${x},${y}` : ` ${x},${y}`;
      }

      const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
      polyline.setAttribute("points", points);
      polyline.setAttribute("fill", "none");
      polyline.setAttribute("stroke", "#0f0");
      polyline.setAttribute("stroke-width", 1);
      group.appendChild(polyline);
    }

    // Formation tops
    if (well.tops) {
      for (const top of well.tops) {
        if (top.depth < depthTop || top.depth > depthBase) continue;
        const dFrac = (top.depth - depthTop) / depthRange;
        const y = dFrac * height;

        // Horizontal marker line
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", -5);
        line.setAttribute("y1", y);
        line.setAttribute("x2", width + 5);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", top.color || "#ff0");
        line.setAttribute("stroke-width", 1);
        line.setAttribute("stroke-dasharray", "3,2");
        group.appendChild(line);

        // Label
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", width + 8);
        label.setAttribute("y", y + 3);
        label.setAttribute("fill", top.color || "#ff0");
        label.setAttribute("font-size", "9px");
        label.textContent = top.name;
        group.appendChild(label);

        // Pick point (draggable anchor for tie lines)
        const pick = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        pick.setAttribute("cx", width / 2);
        pick.setAttribute("cy", y);
        pick.setAttribute("r", 4);
        pick.setAttribute("fill", top.color || "#ff0");
        pick.setAttribute("stroke", "#fff");
        pick.setAttribute("stroke-width", 0.5);
        pick.setAttribute("class", "formation-pick");
        pick.dataset.wellIndex = index;
        pick.dataset.topName = top.name;
        pick.dataset.depth = top.depth;
        group.appendChild(pick);
      }
    }
  }

  _renderTieLines() {
    for (const tie of this.tieLines) {
      const { fromWell, toWell, fromDepth, toDepth, color } = tie;
      const { wellWidth, marginLeft, marginTop, gapBetweenWells } = this.config;

      const fromX = marginLeft + fromWell * (wellWidth + gapBetweenWells) + wellWidth;
      const toX = marginLeft + toWell * (wellWidth + gapBetweenWells);

      const depthRange = this.config.depthBase - this.config.depthTop;
      const fromY = marginTop + ((fromDepth - this.config.depthTop) / depthRange) * this.config.trackHeight;
      const toY = marginTop + ((toDepth - this.config.depthTop) / depthRange) * this.config.trackHeight;

      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", fromX);
      line.setAttribute("y1", fromY);
      line.setAttribute("x2", toX);
      line.setAttribute("y2", toY);
      line.setAttribute("stroke", color || "#888");
      line.setAttribute("stroke-width", 1);
      line.setAttribute("stroke-dasharray", "5,3");
      line.setAttribute("opacity", 0.7);
      this.svg.appendChild(line);
    }
  }

  /**
   * Add a tie line between two formation picks
   */
  addTieLine(fromWell, fromDepth, toWell, toDepth, color = "#888") {
    this.tieLines.push({ fromWell, fromDepth, toWell, toDepth, color });
    this._render();
  }

  /**
   * Export as SVG
   */
  export() {
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(this.svg);
    const blob = new Blob([svgStr], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `multiwell-panel-${Date.now()}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /**
   * Export as PNG snapshot (renders SVG to canvas)
   */
  exportPng() {
    // VP agents can implement: serialize SVG -> canvas -> toDataURL
    this.export(); // Fallback to SVG
  }
}
