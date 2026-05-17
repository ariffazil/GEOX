const GEOX = {
  registry: null,
  graph: null,

  async init() {
    await this.loadRegistry();
    this.populateFilters();
    this.renderHome();
    this.renderCatalog();
    this.renderDomains();
    this.renderScenarios();
    this.setupNavigation();
  },

  async loadRegistry() {
    try {
      const response = await fetch('../registry/registry.json');
      this.registry = await response.json();
      this.buildGraph();
    } catch (e) {
      console.error('Failed to load registry:', e);
    }
  },

  buildGraph() {
    const nodes = this.registry.skills.map(s => ({
      id: s.id,
      domain: s.domain,
      title: s.title,
      status: s.status,
      risk_class: s.risk_class
    }));

    const edges = [];
    this.registry.skills.forEach(skill => {
      (skill.depends_on || []).forEach(dep => {
        edges.push({ from: dep, to: skill.id, type: 'depends_on' });
      });
    });

    this.graph = { nodes, edges };
  },

  populateFilters() {
    const domainSelect = document.getElementById('domainFilter');
    const substrateSelect = document.getElementById('substrateFilter');

    this.registry.domains.forEach(d => {
      domainSelect.innerHTML += `<option value="${d}">${d}</option>`;
    });

    this.registry.substrates.forEach(s => {
      substrateSelect.innerHTML += `<option value="${s}">${s}</option>`;
    });
  },

  renderHome() {
    const cardsContainer = document.getElementById('domainCardsHome');
    cardsContainer.innerHTML = this.registry.domains.map(domain => `
      <div class="domain-card" onclick="showDomain('${domain}')">
        <h3>${domain}</h3>
        <span class="skill-count">3 skills</span>
      </div>
    `).join('');
  },

  renderCatalog(filter = {}) {
    const grid = document.getElementById('skillGrid');
    let skills = [...this.registry.skills];

    if (filter.search) {
      const q = filter.search.toLowerCase();
      skills = skills.filter(s =>
        s.title.toLowerCase().includes(q) ||
        s.id.toLowerCase().includes(q) ||
        s.domain.toLowerCase().includes(q)
      );
    }
    if (filter.domain) skills = skills.filter(s => s.domain === filter.domain);
    if (filter.substrate) skills = skills.filter(s => s.substrates?.includes(filter.substrate));
    if (filter.risk) skills = skills.filter(s => s.risk_class === filter.risk);

    grid.innerHTML = skills.map(skill => this.renderSkillCard(skill)).join('');
  },

  renderSkillCard(skill) {
    return `
      <div class="skill-card" onclick="showSkillDetail('${skill.id}')">
        <div class="skill-header">
          <span class="skill-domain">${skill.domain}</span>
          <span class="skill-risk ${skill.risk_class}">${skill.risk_class}</span>
        </div>
        <h3 class="skill-title">${skill.title}</h3>
        <p class="skill-id">${skill.id}</p>
        <div class="skill-substrates">
          ${(skill.substrates || []).map(s => `<span class="substrate-tag ${s}">${s}</span>`).join('')}
        </div>
      </div>
    `;
  },

  renderDomains() {
    const container = document.getElementById('domainsList');
    container.innerHTML = this.registry.domains.map(domain => {
      const domainSkills = this.registry.skills.filter(s => s.domain === domain);
      return `
        <div class="domain-section" id="domain-${domain}">
          <h2 class="domain-name">${domain}</h2>
          <div class="domain-skills">
            ${domainSkills.map(s => this.renderSkillCard(s)).join('')}
          </div>
        </div>
      `;
    }).join('');
  },

  renderScenarios() {
    const scenarios = [
      {
        name: 'Flood Watch',
        skills: ['geox.water.floodplain-and-flow', 'geox.hazards.multi-risk-escalation', 'geox.terrain.drainage-structure', 'geox.atmo.weather-state', 'geox.time.monitoring-triggers']
      },
      {
        name: 'Port Operations',
        skills: ['geox.water.maritime-state', 'geox.mobility.route-viability', 'geox.infrastructure.critical-node-watch', 'geox.sensing.observation-intake', 'geox.mobility.fleet-patterns']
      },
      {
        name: 'Seismic Watch',
        skills: ['geox.hazards.seismic-and-ground-shift', 'geox.hazards.anomaly-detection', 'geox.geodesy.position-fix-fusion', 'geox.sensing.signal-classification', 'geox.time.regime-shift']
      },
      {
        name: 'Urban Growth',
        skills: ['geox.terrain.surface-access', 'geox.infrastructure.network-topology', 'geox.governance.legal-jurisdiction', 'geox.time.forecast-branching', 'geox.orchestration.multi-agent-decomposition']
      }
    ];

    const container = document.getElementById('scenarioCards');
    container.innerHTML = scenarios.map(scenario => `
      <div class="scenario-card">
        <h3>${scenario.name}</h3>
        <div class="scenario-skills">
          ${scenario.skills.map(id => {
            const skill = this.registry.skills.find(s => s.id === id);
            return skill ? `<span class="scenario-skill" onclick="showSkillDetail('${id}')">${skill.title}</span>` : '';
          }).join('')}
        </div>
      </div>
    `).join('');
  },

  showSkillDetail(id) {
    const skill = this.registry.skills.find(s => s.id === id);
    if (!skill) return;

    const container = document.getElementById('skillDetailContent');
    container.innerHTML = `
      <div class="skill-detail">
        <div class="skill-detail-header">
          <span class="skill-domain">${skill.domain}</span>
          <span class="skill-risk ${skill.risk_class}">${skill.risk_class}</span>
          <span class="skill-status">${skill.status}</span>
        </div>
        <h1>${skill.title}</h1>
        <p class="skill-id">${skill.id}</p>

        <div class="skill-meta">
          <div class="meta-section">
            <h4>Substrates</h4>
            <div class="substrate-tags">
              ${(skill.substrates || []).map(s => `<span class="substrate-tag ${s}">${s}</span>`).join('')}
            </div>
          </div>
          <div class="meta-section">
            <h4>Scales</h4>
            <div class="tag-list">${(skill.scales || []).join(', ')}</div>
          </div>
          <div class="meta-section">
            <h4>Horizons</h4>
            <div class="tag-list">${(skill.horizons || []).join(', ')}</div>
          </div>
        </div>

        <div class="skill-contract">
          <h4>Inputs</h4>
          <div class="tag-list">${(skill.inputs || []).join(', ')}</div>
          <h4>Outputs</h4>
          <div class="tag-list">${(skill.outputs || []).join(', ')}</div>
        </div>

        ${(skill.depends_on || []).length > 0 ? `
          <div class="skill-dependencies">
            <h4>Depends On</h4>
            <div class="dep-list">
              ${skill.depends_on.map(id => {
                const dep = this.registry.skills.find(s => s.id === id);
                return dep ? `<span class="dep-skill" onclick="showSkillDetail('${id}')">${dep.title}</span>` : `<span class="dep-skill">${id}</span>`;
              }).join('')}
            </div>
          </div>
        ` : ''}

        <div class="skill-surface">
          <h4>Surface Availability</h4>
          <div class="surface-tags">
            ${skill.mcp_resource ? '<span class="surface-tag resource">MCP Resource</span>' : ''}
            ${skill.mcp_prompt ? '<span class="surface-tag prompt">MCP Prompt</span>' : ''}
            ${skill.mcp_tool ? '<span class="surface-tag tool">MCP Tool</span>' : ''}
          </div>
        </div>
      </div>
    `;

    this.showView('skill-detail');
  },

  setupNavigation() {
    document.querySelectorAll('nav a').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const view = e.target.getAttribute('href').substring(1);
        this.showView(view);
      });
    });

    document.getElementById('searchInput')?.addEventListener('input', (e) => {
      this.applyFilters();
    });
    document.getElementById('domainFilter')?.addEventListener('change', () => this.applyFilters());
    document.getElementById('substrateFilter')?.addEventListener('change', () => this.applyFilters());
    document.getElementById('riskFilter')?.addEventListener('change', () => this.applyFilters());
  },

  applyFilters() {
    this.renderCatalog({
      search: document.getElementById('searchInput')?.value || '',
      domain: document.getElementById('domainFilter')?.value || '',
      substrate: document.getElementById('substrateFilter')?.value || '',
      risk: document.getElementById('riskFilter')?.value || ''
    });
  },

  showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(viewId)?.classList.add('active');
    document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
    document.querySelector(`nav a[href="#${viewId}"]`)?.classList.add('active');
  }
};

function showDomain(domain) {
  showView('domains');
  document.getElementById(`domain-${domain}``)?.scrollIntoView({ behavior: 'smooth' });
}

function showSkillDetail(id) {
  GEOX.showSkillDetail(id);
}

function showView(viewId) {
  GEOX.showView(viewId);
}

document.addEventListener('DOMContentLoaded', () => GEOX.init());
