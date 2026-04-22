/**
 * XPlot2D.js — 2D Crossplot (Canvas)
 * ===================================
 * Vp/Vs, NPHI/RHOB, M*N crossplots with formation template overlays.
 */

class XPlot2D {
  constructor(containerId, config = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) throw new Error(`XPlot2D: container #${containerId} not found`);

    this.config = {
      width: config.width || 500,
      height: config.height || 500,
      padding: config.padding || 50,
      pointRadius: config.pointRadius || 3,
      ...config
    };

    this.canvas = document.createElement("canvas");
    this.canvas.width = this.config.width;
    this.canvas.height = this.config.height;
    this.canvas.style.background = "#0f0f1a";
    this.canvas.style.border = "1px solid #333";
    this.container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext("2d");

    this.data = [];
    this.selection = [];  // Selected points (brushed)
  }

  /**
   * Load data array: [{x, y, depth, label?}, ...]
   */
  load(data) {
    this.data = data;
    this._autoScale();
    this.draw();
  }

  /**
   * Set explicit axis ranges
   */
  setRange(xMin, xMax, yMin, yMax) {
    this.xRange = [xMin, xMax];
    this.yRange = [yMin, yMax];
    this.draw();
  }

  _autoScale() {
    if (!this.data.length) return;
    const xs = this.data.map(d => d.x);
    const ys = this.data.map(d => d.y);
    const xPad = (Math.max(...xs) - Math.min(...xs)) * 0.05;
    const yPad = (Math.max(...ys) - Math.min(...ys)) * 0.05;
    this.xRange = [Math.min(...xs) - xPad, Math.max(...xs) + xPad];
    this.yRange = [Math.min(...ys) - yPad, Math.max(...ys) + yPad];
  }

  _toCanvas(x, y) {
    const { width, height, padding } = this.config;
    const xFrac = (x - this.xRange[0]) / (this.xRange[1] - this.xRange[0]);
    const yFrac = (y - this.yRange[0]) / (this.yRange[1] - this.yRange[0]);
    return {
      x: padding + xFrac * (width - 2 * padding),
      y: height - padding - yFrac * (height - 2 * padding)
    };
  }

  draw() {
    const { width, height, padding } = this.config;
    const ctx = this.ctx;

    // Clear
    ctx.fillStyle = "#0f0f1a";
    ctx.fillRect(0, 0, width, height);

    // Grid
    ctx.strokeStyle = "#222";
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 10; i++) {
      const x = padding + (i / 10) * (width - 2 * padding);
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, height - padding);
      ctx.stroke();

      const y = padding + (i / 10) * (height - 2 * padding);
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    // Axes
    ctx.strokeStyle = "#888";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();

    // Axis labels
    ctx.fillStyle = "#aaa";
    ctx.font = "10px monospace";
    ctx.textAlign = "center";

    // X ticks
    for (let i = 0; i <= 5; i++) {
      const frac = i / 5;
      const val = this.xRange[0] + frac * (this.xRange[1] - this.xRange[0]);
      const pos = padding + frac * (width - 2 * padding);
      ctx.fillText(val.toFixed(2), pos, height - padding + 15);
    }

    // Y ticks
    ctx.textAlign = "right";
    for (let i = 0; i <= 5; i++) {
      const frac = i / 5;
      const val = this.yRange[0] + frac * (this.yRange[1] - this.yRange[0]);
      const pos = height - padding - frac * (height - 2 * padding);
      ctx.fillText(val.toFixed(2), padding - 8, pos + 3);
    }

    // Draw template regions
    this._drawTemplates(ctx);

    // Data points
    for (const pt of this.data) {
      const c = this._toCanvas(pt.x, pt.y);
      ctx.beginPath();
      ctx.arc(c.x, c.y, this.config.pointRadius, 0, Math.PI * 2);
      ctx.fillStyle = pt.color || "#0f0";
      ctx.fill();
    }

    // Selection highlight
    for (const idx of this.selection) {
      const pt = this.data[idx];
      if (!pt) continue;
      const c = this._toCanvas(pt.x, pt.y);
      ctx.beginPath();
      ctx.arc(c.x, c.y, this.config.pointRadius + 3, 0, Math.PI * 2);
      ctx.strokeStyle = "#ff0";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }

  _drawTemplates(ctx) {
    // Vp/Vs lithology template
    if (this.xRange[1] > 5 && this.yRange[1] > 2) {
      // Sandstone line
      ctx.strokeStyle = "rgba(0, 255, 0, 0.3)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      const p1 = this._toCanvas(1.6, 2.0);
      const p2 = this._toCanvas(1.6, 2.8);
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }
  }

  /**
   * Brush select: highlight points within rectangle
   */
  brush(x1, y1, x2, y2) {
    const [xMin, xMax] = [Math.min(x1, x2), Math.max(x1, x2)];
    const [yMin, yMax] = [Math.min(y1, y2), Math.max(y1, y2)];

    this.selection = this.data
      .map((d, i) => ({ ...d, i }))
      .filter(d => d.x >= xMin && d.x <= xMax && d.y >= yMin && d.y <= yMax)
      .map(d => d.i);

    this.draw();
    return this.selection;
  }

  /**
   * Export as PNG
   */
  export() {
    const link = document.createElement("a");
    link.download = `xplot-${Date.now()}.png`;
    link.href = this.canvas.toDataURL("image/png");
    link.click();
  }
}
