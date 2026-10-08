// GEOX Seismic Vision — MCP-Apps scaffold (SEP-1865)
// Standalone fallback. MCP hydration via window.GEOX_MCP when host injects it.
(function () {
  const $ = (id) => document.getElementById(id);
  const setStatus = (txt) => { const el = $("mcpStatus"); if (el) el.textContent = txt; };

  // Probe for MCP host context (apps that wrap us via postMessage / iframe / Shadow Root)
  const probeMcp = () => {
    if (window.parent && window.parent !== window) setStatus("EMBEDDED");
    else if (window.GEOX_MCP) setStatus("MCP-HYDRATED");
    else setStatus("STANDALONE");
  };
  probeMcp();

  // Render a synthetic 2D section until a real seismic ingest lands
  const render = () => {
    const il = parseInt($("inlineX").value || "200", 10);
    const xl = parseInt($("crosslineX").value || "300", 10);
    const cs = $("colorScale").value;
    const nt = 200, nx = 200;
    const t = Array.from({ length: nt }, (_, i) => i * 2); // 0..400 ms
    const x = Array.from({ length: nx }, (_, j) => j);
    const z = [];
    for (let i = 0; i < nt; i++) {
      const row = [];
      for (let j = 0; j < nx; j++) {
        const horizon = 80 + 0.2 * j + 0.05 * i;
        const v = Math.sin(((i - horizon) / 6) * Math.PI) * Math.exp(-((i - horizon) ** 2) / 600);
        row.push(v + 0.05 * (Math.random() - 0.5));
      }
      z.push(row);
    }
    const data = [{ z, x, y: t, type: "heatmap", colorscale: cs, reversescale: true }];
    Plotly.newPlot("seismicPlot", data, {
      title: `Synthetic inline ${il} / crossline ${xl}`,
      xaxis: { title: "trace" },
      yaxis: { title: "TWT (ms)", autorange: "reversed" },
      margin: { t: 36, r: 12, b: 36, l: 48 }
    }, { responsive: true });

    // Horizons stub
    const ul = $("horizonList");
    if (ul) {
      ul.innerHTML = "";
      ["H1 ~ 1.6s", "H2 ~ 2.0s", "H3 ~ 2.4s"].forEach((h) => {
        const li = document.createElement("li"); li.textContent = h; ul.appendChild(li);
      });
    }
  };

  document.addEventListener("DOMContentLoaded", () => {
    const btn = $("renderBtn");
    if (btn) btn.addEventListener("click", render);
    render();
  });
})();