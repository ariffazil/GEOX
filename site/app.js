/**
 * GEOX Site App
 * Client-side search and filter for skills catalog
 * ═══════════════════════════════════════════════════════════════════════════════
 */

// Global state
let registry = null;
let currentFilter = {
  search: '',
  domains: new Set(),
  substrates: new Set()
};

// Initialize
async function init() {
  try {
    const response = await fetch('registry.json');
    registry = await response.json();
    renderFilters();
    renderSkills();
    setupSearch();
  } catch (err) {
    console.error('Failed to load registry:', err);
    document.querySelector('.skills-section').innerHTML = 
      '<div class="empty-state">Failed to load skill registry</div>';
  }
}

// Setup search input
function setupSearch() {
  const searchInput = document.getElementById('skill-search');
  if (!searchInput) return;
  
  searchInput.addEventListener('input', (e) => {
    currentFilter.search = e.target.value.toLowerCase();
    renderSkills();
  });
}

// Toggle domain filter
function toggleDomain(domainId) {
  if (currentFilter.domains.has(domainId)) {
    currentFilter.domains.delete(domainId);
  } else {
    currentFilter.domains.add(domainId);
  }
  updateChipStyles();
  renderSkills();
}

// Toggle substrate filter
function toggleSubstrate(substrate) {
  if (currentFilter.substrates.has(substrate)) {
    currentFilter.substrates.delete(substrate);
  } else {
    currentFilter.substrates.add(substrate);
  }
  updateChipStyles();
  renderSkills();
}

// Update chip active states
function updateChipStyles() {
  document.querySelectorAll('.chip-domain').forEach(chip => {
    const domain = chip.dataset.domain;
    chip.classList.toggle('active', currentFilter.domains.has(domain));
  });
  document.querySelectorAll('.chip-substrate').forEach(chip => {
    const substrate = chip.dataset.substrate;
    chip.classList.toggle('active', currentFilter.substrates.has(substrate));
  });
}

// Render filter chips
function renderFilters() {
  const domainContainer = document.getElementById('domain-filters');
  const substrateContainer = document.getElementById('substrate-filters');
  
  if (domainContainer) {
    domainContainer.innerHTML = registry.domains.map(d => {
      const count = d.skills.length;
      return `<button class="chip chip-domain" data-domain="${d.id}" onclick="toggleDomain('${d.id}')">
        ${d.name} <span class="count">${count}</span>
      </button>`;
    }).join('');
  }
  
  if (substrateContainer) {
    const substrates = registry.meta.substrates;
    substrateContainer.innerHTML = substrates.map(s => {
      const count = Object.values(registry.skills).filter(
        sk => sk.substrates.includes(s)
      ).length;
      return `<button class="chip chip-substrate" data-substrate="${s}" onclick="toggleSubstrate('${s}')">
        ${s} <span class="count">${count}</span>
      </button>`;
    }).join('');
  }
}

// Check if skill matches current filter
function matchesFilter(skill) {
  // Search text filter
  if (currentFilter.search) {
    const searchIn = [
      skill.name,
      skill.description,
      skill.id,
      ...skill.inputs,
      ...skill.outputs
    ].join(' ').toLowerCase();
    if (!searchIn.includes(currentFilter.search)) {
      return false;
    }
  }
  
  // Domain filter
  if (currentFilter.domains.size > 0) {
    if (!currentFilter.domains.has(skill.domain)) {
      return false;
    }
  }
  
  // Substrate filter
  if (currentFilter.substrates.size > 0) {
    const hasMatchingSubstrate = skill.substrates.some(s => 
      currentFilter.substrates.has(s)
    );
    if (!hasMatchingSubstrate) {
      return false;
    }
  }
  
  return true;
}

// Render skills grid
function renderSkills() {
  const container = document.getElementById('skills-container');
  if (!container || !registry) return;
  
  const domains = registry.domains;
  let hasAnySkills = false;
  
  let html = '';
  
  domains.forEach(domain => {
    const domainSkills = domain.skills
      .map(id => registry.skills[id])
      .filter(skill => matchesFilter(skill));
    
    if (domainSkills.length === 0) return;
    hasAnySkills = true;
    
    html += `
      <div class="domain-group">
        <div class="domain-header">
          <h3>${domain.name}</h3>
          <span class="count">${domainSkills.length} skills</span>
        </div>
        <div class="skills-grid">
          ${domainSkills.map(skill => renderSkillCard(skill)).join('')}
        </div>
      </div>
    `;
  });
  
  if (!hasAnySkills) {
    html = `
      <div class="empty-state">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
        <p>No skills match your filters</p>
      </div>
    `;
  }
  
  container.innerHTML = html;
  
  // Update stats
  const totalSkills = Object.values(registry.skills).filter(matchesFilter).length;
  const statsEl = document.getElementById('stats-count');
  if (statsEl) {
    statsEl.textContent = `${totalSkills} of ${registry.meta.total_skills} skills`;
  }
}

// Render single skill card
function renderSkillCard(skill) {
  const complexityDots = Array(5).fill(0).map((_, i) => 
    `<span class="complexity-dot ${i < skill.complexity ? 'filled' : ''}"></span>`
  ).join('');
  
  const substrateTags = skill.substrates.map(s => 
    `<span class="tag substrate-${s}">${s}</span>`
  ).join('');
  
  return `
    <a href="skills/${skill.id}.html" class="skill-card">
      <div class="skill-header">
        <span class="skill-name">${skill.name}</span>
        <span class="skill-complexity" title="Complexity: ${skill.complexity}/5">
          ${complexityDots}
        </span>
      </div>
      <p class="skill-desc">${skill.description}</p>
      <div class="skill-meta">
        ${substrateTags}
      </div>
    </a>
  `;
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
