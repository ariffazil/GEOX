import { App } from "@modelcontextprotocol/ext-apps";

// ── DOM refs ──
const statusBadge = document.getElementById("status-badge")!;
const loadingState = document.getElementById("loading-state")!;
const basinContent = document.getElementById("basin-content")!;
const basinOverview = document.getElementById("basin-overview")!;
const governanceInfo = document.getElementById("governance-info")!;
const fairwaysList = document.getElementById("fairways-list")!;
const risksList = document.getElementById("risks-list")!;
const contradictionsList = document.getElementById("contradictions-list")!;
const actionsList = document.getElementById("actions-list")!;
const refreshBtn = document.getElementById("refresh-btn")!;
const toastEl = document.getElementById("toast")!;

// ── Helpers ──
function showToast(msg: string) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 2500);
}

function setStatus(text: string, cls: string) {
  statusBadge.textContent = text;
  statusBadge.className = `status ${cls}`;
}

function renderBasinData(data: any) {
  // Extract basin info
  const artifact = data.primary_artifact || data;
  const provenance = data.provenance || {};
  const apex = data.apex || {};

  // ── Basin Overview ──
  basinOverview.innerHTML = `
    <div class="value-row"><span class="label">Basin</span><span class="value">${artifact.basin_name || "—"}</span></div>
    <div class="value-row"><span class="label">Mode</span><span class="value">${artifact.mode || "—"}</span></div>
    <div class="value-row"><span class="label">Claim Tag</span><span class="value">${data.claim_tag || "—"}</span></div>
    <div class="value-row"><span class="label">Claim State</span><span class="value">${data.claim_state || "—"}</span></div>
    <div class="value-row"><span class="label">Uncertainty</span><span class="value">${data.uncertainty || "—"}</span></div>
    <div class="value-row"><span class="label">Domain Law</span><span class="value">${provenance.domain_law || "—"}</span></div>
    <div class="value-row"><span class="label">GeoX Version</span><span class="value">${provenance.geox_version || "—"}</span></div>
  `;

  // ── Governance ──
  const g = apex.gates || {};
  const verdict = apex.verdict || "—";
  let verdictColor = "yellow";
  if (verdict === "SEAL") verdictColor = "green";
  if (verdict === "HOLD") verdictColor = "red";

  governanceInfo.innerHTML = `
    <div class="value-row"><span class="label">Verdict</span><span class="value" style="color:${verdictColor === 'green' ? '#3fb950' : verdictColor === 'red' ? '#f85149' : '#d29922'}">${verdict}</span></div>
    <div class="value-row"><span class="label">G-Score</span><span class="value">${(apex.G ?? 0).toFixed(3)}</span></div>
    <div style="margin:8px 0 4px">
      ${Object.entries(g).map(([k, v]: any) => `
        <div class="value-row" style="font-size:12px">
          <span class="label">${k}</span>
          <span class="value" style="color:${v?.pass ? '#3fb950' : '#f85149'}">
            ${v?.pass ? '✅' : '❌'} ${(v?.score ?? 0).toFixed(2)}
          </span>
        </div>
      `).join('')}
    </div>
    <div class="score-bar">
      <div class="fill ${verdictColor}" style="width:${Math.min((apex.G ?? 0) * 100, 100)}%"></div>
    </div>
  `;

  // ── Play Fairways ──
  const fairways = artifact.play_fairways || [];
  if (fairways.length === 0) {
    fairwaysList.innerHTML = '<div class="empty-state">No play fairways identified</div>';
  } else {
    fairwaysList.innerHTML = fairways.map((fw: any) => `
      <div class="fairway-item">
        <strong>${fw.name || "Unnamed"}</strong>
        ${fw.pos ? `<div style="color:#8b949e;font-size:12px;margin-top:2px">POS: ${fw.pos}</div>` : ''}
        ${fw.volume ? `<div style="color:#8b949e;font-size:12px">Volume: ${fw.volume}</div>` : ''}
      </div>
    `).join('');
  }

  // ── Risk Register ──
  const risks = artifact.risk_register || [];
  if (risks.length === 0) {
    risksList.innerHTML = '<div class="empty-state">No risks registered</div>';
  } else {
    risksList.innerHTML = risks.map((r: any) => `
      <div class="risk-item">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <strong>${r.name || r.risk || "Risk"}</strong>
          <span class="risk-score ${r.severity === 'high' || r.level === 'high' ? 'risk-high' : r.severity === 'medium' || r.level === 'medium' ? 'risk-medium' : 'risk-low'}">
            ${r.severity || r.level || "unknown"}
          </span>
        </div>
        <div style="color:#8b949e;font-size:12px;margin-top:2px">${r.description || r.detail || ""}</div>
      </div>
    `).join('');
  }

  // ── Contradictions ──
  const contradictions = artifact.contradictions || [];
  const missing = artifact.missing_evidence || [];
  if (contradictions.length === 0 && missing.length === 0) {
    contradictionsList.innerHTML = '<div class="empty-state">No contradictions or missing evidence</div>';
  } else {
    const items = [
      ...contradictions.map((c: any) => `<div class="contradiction-item">⚠️ <strong>Contradiction:</strong> ${typeof c === 'string' ? c : c.description || JSON.stringify(c)}</div>`),
      ...missing.map((m: any) => `<div class="contradiction-item">❓ <strong>Missing:</strong> ${typeof m === 'string' ? m : m.evidence || m.description || JSON.stringify(m)}</div>`),
    ];
    contradictionsList.innerHTML = items.join('');
  }

  // ── Next Best Actions ──
  const actions = artifact.next_best_actions || [];
  if (actions.length === 0) {
    actionsList.innerHTML = '<div class="empty-state">No suggested actions</div>';
  } else {
    actionsList.innerHTML = actions.map((a: any) => `
      <div class="risk-item">
        <strong>${a.tool || a.action || "Action"}</strong>
        <div style="color:#8b949e;font-size:12px;margin-top:2px">${a.reason || a.description || ""}</div>
      </div>
    `).join('');
  }

  setStatus("Loaded", "loaded");
}

function showError(err: any) {
  loadingState.style.display = "flex";
  loadingState.textContent = `Error: ${err?.message || err || "Unknown error"}`;
  basinContent.style.display = "none";
  setStatus("Error", "error");
}

// ── App init ──
const app = new App({ name: "GEOX Basin Panel", version: "1.0.0" });

// Handle initial tool result pushed by host
app.ontoolresult = (result: any) => {
  loadingState.style.display = "none";
  basinContent.style.display = "block";

  try {
    const content = result.content?.find((c: any) => c.type === "text")?.text;
    if (content) {
      const data = JSON.parse(content);
      renderBasinData(data);
      showToast("Basin data loaded");
    } else {
      showError("No text content in tool result");
    }
  } catch (e) {
    showError(e);
  }
};

// Wire refresh button
refreshBtn.addEventListener("click", async () => {
  refreshBtn.disabled = true;
  refreshBtn.textContent = "⏳ Loading...";
  setStatus("Loading", "pending");

  try {
    const result = await app.callServerTool({
      name: "geox_basin",
      arguments: { mode: "profile", name: "Sabah Basin" },
    });
    const content = result.content?.find((c: any) => c.type === "text")?.text;
    if (content) {
      renderBasinData(JSON.parse(content));
      showToast("Data refreshed");
    }
  } catch (e) {
    showError(e);
  } finally {
    refreshBtn.disabled = false;
    refreshBtn.textContent = "🔄 Refresh Data";
  }
});

// Connect to host (establishes postMessage channel)
app.connect();
