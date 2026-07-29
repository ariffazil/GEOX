// GEOX LEM Dashboard — live tool count from health endpoint
(async function() {
  try {
    const resp = await fetch('/health');
    const d = await resp.json();
    const stats = document.getElementById('stats');
    const toolList = document.getElementById('toolList');
    if (stats) {
      stats.innerHTML = `
        <div class="stat"><div class="stat-num">${d.canonical_tools || 33}</div><div class="stat-label">Public Tools</div></div>
        <div class="stat"><div class="stat-num">5</div><div class="stat-label">LEM Engines</div></div>
        <div class="stat"><div class="stat-num">${d.tools_loaded || 33}</div><div class="stat-label">Live Tools</div></div>
        <div class="stat"><div class="stat-num">${d.surface_drift?.drift_count || 0}</div><div class="stat-label">Surface Drift</div></div>
      `;
    }
    // Fetch active MCP tools (requires MCP init — fallback to static)
    if (toolList) {
      toolList.innerHTML = '<div class="tool-item">Live tools via MCP tools/list — requires authenticated session</div>';
    }
  } catch(e) {
    console.log('Health fetch failed:', e);
  }
})();

// Verb interactions
document.querySelectorAll('.intent-card').forEach(card => {
  card.addEventListener('click', () => {
    const verb = card.dataset.verb;
    const next = document.getElementById('nextAction');
    if (next) next.textContent = `→ ${verb} (MCP tool)`;
  });
});
