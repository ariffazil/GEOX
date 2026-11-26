import { App } from "@modelcontextprotocol/ext-apps";

interface QuarantineRow {
  file: string;
  curve: string;
  status: "PASS" | "WARN" | "QUARANTINE";
  fault: string;
}

const DEFAULT_ROWS: QuarantineRow[] = [
  { file: "SYNTH-DW-01_run1.las", curve: "GR_R1", status: "QUARANTINE", fault: "KB_DATUM_SHIFT" },
  { file: "SYNTH-DW-01_run1.las", curve: "VPVS_CORRUPT", status: "QUARANTINE", fault: "UNIT_FACTOR_32808" },
  { file: "SYNTH-DW-01_run1.las", curve: "NPHI_BAD", status: "QUARANTINE", fault: "POROSITY_X100_MISMATCH" },
  { file: "SYNTH-DW-01_run1.las", curve: "DTCO_BAD", status: "QUARANTINE", fault: "SONIC_UNIT_HEADER_LIE" },
  { file: "SYNTH-DW-01_stub1.las", curve: "*", status: "QUARANTINE", fault: "SENTINEL_STUB_BLINDSPOT" },
  { file: "SYNTH-DW-01_disguised_las.csv", curve: "*", status: "WARN", fault: "IDENTITY_TDR_FORMAT_DRIFT" },
  { file: "SYNTH-DW-01_run2.las", curve: "RHOB/NPHI/NMR", status: "QUARANTINE", fault: "ROCK_PHYSICS_TRAP" },
  { file: "SYNTH-DW-01_tops.json", curve: "BIOSTRAT", status: "QUARANTINE", fault: "STRAT_AGE_INVERSION" },
];

const app = new App({ name: "geox-well-forensic-desk", version: "1.0.0" });
const statusEl = document.getElementById("status")!;
const qBody = document.getElementById("q-body")!;
const slider = document.getElementById("shift-slider") as HTMLInputElement;
const shiftVal = document.getElementById("shift-val")!;
const corrReadout = document.getElementById("corr-readout")!;
const svg = document.getElementById("track-svg")!;

let currentRows: QuarantineRow[] = DEFAULT_ROWS;
let activeFilter: string | null = null;

function renderMatrix(): void {
  const rows = activeFilter ? currentRows.filter((r) => r.fault === activeFilter) : currentRows;
  qBody.innerHTML = rows
    .map(
      (r) =>
        `<tr class="clickable" data-fault="${r.fault}"><td>${r.file}</td><td>${r.curve}</td><td><span class="badge ${r.status}">${r.status}</span></td><td><code>${r.fault}</code></td></tr>`,
    )
    .join("");
  qBody.querySelectorAll("tr").forEach((tr) => {
    tr.addEventListener("click", () => {
      const f = tr.getAttribute("data-fault");
      activeFilter = activeFilter === f ? null : f;
      statusEl.textContent = activeFilter ? `Filtered: ${activeFilter} (click again to clear)` : "Showing all rows";
      renderMatrix();
    });
  });
}

function renderTracks(shiftM: number): void {
  const r = Math.max(0.05, Math.exp(-Math.pow((shiftM + 30) / 14, 2)));
  shiftVal.textContent = `${shiftM.toFixed(1)} m`;
  corrReadout.textContent = `Pearson r = ${r.toFixed(3)} ${Math.abs(shiftM + 30) <= 1 ? "(PEAK ALIGNED!)" : "(peak at -30 m)"}`;
  const ptsR2: string[] = [];
  const ptsR1: string[] = [];
  const ptsVp: string[] = [];
  const ptsNphi: string[] = [];
  const ptsNmr: string[] = [];
  const ptsRt: string[] = [];
  for (let i = 0; i <= 40; i++) {
    const y = 12 + i * 5.4;
    const gr2 = 55 + 32 * Math.sin(i / 4.5);
    const gr1 = 55 + 32 * Math.sin((i + (shiftM + 30) / 8) / 4.5);
    const inTrap = i >= 28 && i <= 36;
    ptsR2.push(`${(20 + gr2).toFixed(1)},${y.toFixed(1)}`);
    ptsR1.push(`${(20 + gr1).toFixed(1)},${y.toFixed(1)}`);
    ptsVp.push(`${(195 + (inTrap ? 95 : 42)).toFixed(1)},${y.toFixed(1)}`);
    ptsNphi.push(`${(380 + (inTrap ? 78 : 35)).toFixed(1)},${y.toFixed(1)}`);
    ptsNmr.push(`${(380 + (inTrap ? 28 : 31)).toFixed(1)},${y.toFixed(1)}`);
    ptsRt.push(`${(535 + (inTrap ? 18 : 68)).toFixed(1)},${y.toFixed(1)}`);
  }
  const shadePoly = [...ptsNphi, ...ptsNmr.slice().reverse()].join(" ");
  svg.innerHTML = `
    <rect x="0" y="0" width="640" height="240" fill="#0f1620"/>
    <rect x="0" y="163" width="640" height="44" fill="#e4572e" fill-opacity="0.14"/>
    <line x1="160" y1="0" x2="160" y2="240" stroke="#293548"/>
    <line x1="320" y1="0" x2="320" y2="240" stroke="#293548"/>
    <line x1="480" y1="0" x2="480" y2="240" stroke="#293548"/>
    <text x="8" y="14" fill="#94a3b8" font-size="10">GR_R1 vs GR_R2</text>
    <text x="168" y="14" fill="#94a3b8" font-size="10">Sonic / VpVs Anomaly</text>
    <text x="328" y="14" fill="#94a3b8" font-size="10">NPHI vs PHIE_NMR (OH)</text>
    <text x="488" y="14" fill="#94a3b8" font-size="10">RT / SW = 1.0</text>
    <polygon points="${shadePoly}" fill="#fbbf24" fill-opacity="0.28"/>
    <polyline points="${ptsR2.join(" ")}" fill="none" stroke="#34d399" stroke-width="1.8"/>
    <polyline points="${ptsR1.join(" ")}" fill="none" stroke="#fb7185" stroke-width="1.5" stroke-dasharray="4 2"/>
    <polyline points="${ptsVp.join(" ")}" fill="none" stroke="#e4572e" stroke-width="1.8"/>
    <polyline points="${ptsNphi.join(" ")}" fill="none" stroke="#fbbf24" stroke-width="1.6"/>
    <polyline points="${ptsNmr.join(" ")}" fill="none" stroke="#38bdf8" stroke-width="1.6"/>
    <polyline points="${ptsRt.join(" ")}" fill="none" stroke="#a78bfa" stroke-width="1.8"/>
  `;
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab, .view").forEach((el) => el.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.getAttribute("data-view")!)?.classList.add("active");
  });
});

slider.addEventListener("input", () => renderTracks(Number(slider.value)));

async function persistDecision(decision: "ACCEPT_QUARANTINE" | "FLAG_REVIEW"): Promise<void> {
  statusEl.textContent = `Persisting ${decision}...`;
  try {
    await app.callServerTool({
      name: "geox_well_pda",
      arguments: { mode: "triage_decision", payload: { decision, well: "SYNTH-DW-01" } },
    });
    statusEl.textContent = `Saved: ${decision}`;
  } catch {
    statusEl.textContent = `Queued offline: ${decision}`;
  }
}

document.getElementById("btn-accept")!.addEventListener("click", () => void persistDecision("ACCEPT_QUARANTINE"));
document.getElementById("btn-flag")!.addEventListener("click", () => void persistDecision("FLAG_REVIEW"));

app.ontoolresult = (result: any) => {
  const sc = result?.structuredContent?.data;
  if (sc && Array.isArray(sc.quarantine_matrix) && sc.quarantine_matrix.length > 0) {
    currentRows = sc.quarantine_matrix;
    renderMatrix();
    statusEl.textContent = `Loaded ${currentRows.length} rows (${result.structuredContent.verdict})`;
  }
};

renderMatrix();
renderTracks(0);
app.connect().catch(() => {
  /* standalone preview mode */
});
