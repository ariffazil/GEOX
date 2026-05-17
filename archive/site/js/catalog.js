document.addEventListener('DOMContentLoaded', async () => {
    const skillsContainer = document.getElementById('skills-container');
    const domainFilters = document.getElementById('domain-filters');
    const substrateFilters = document.getElementById('substrate-filters');
    const skillSearch = document.getElementById('skill-search');
    const statsCount = document.getElementById('stats-count');

    let allSkills = [];
    let activeDomain = 'all';
    let activeSubstrate = 'all';

    try {
        const response = await fetch('registry.json');
        const data = await response.json();
        
        // Convert skills object to array
        allSkills = Object.values(data.skills);
        
        renderFilters(data.domains, data.meta.substrates);
        renderSkills(allSkills);
        updateStats(allSkills.length);

    } catch (error) {
        console.error('Error loading registry:', error);
        skillsContainer.innerHTML = '<p class="error">Failed to load skill registry. Verification required.</p>';
    }

    function renderFilters(domains, substrates) {
        // Domains
        let domainHtml = '<div class="filter-chip active" data-domain="all">ALL DOMAINS</div>';
        domains.forEach(d => {
            domainHtml += `<div class="filter-chip" data-domain="${d.id}">${d.name.toUpperCase()}</div>`;
        });
        domainFilters.innerHTML = domainHtml;

        // Substrates
        let substrateHtml = '<div class="filter-chip active" data-substrate="all">ALL SUBSTRATES</div>';
        substrates.forEach(s => {
            substrateHtml += `<div class="filter-chip" data-substrate="${s}">${s.toUpperCase()}</div>`;
        });
        substrateFilters.innerHTML = substrateHtml;

        // Event Listeners
        domainFilters.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                domainFilters.querySelector('.active').classList.remove('active');
                chip.classList.add('active');
                activeDomain = chip.dataset.domain;
                filterAndRender();
            });
        });

        substrateFilters.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                substrateFilters.querySelector('.active').classList.remove('active');
                chip.classList.add('active');
                activeSubstrate = chip.dataset.substrate;
                filterAndRender();
            });
        });
    }

    function renderSkills(skills) {
        if (skills.length === 0) {
            skillsContainer.innerHTML = '<p class="text-muted">No skills match the current filter criteria.</p>';
            return;
        }

        skillsContainer.innerHTML = skills.map(skill => `
            <article class="skill-card">
                <div class="skill-domain">${skill.domain}</div>
                <h3 class="skill-title">${skill.name}</h3>
                <p class="skill-description">${skill.description}</p>
                <div class="skill-tags">
                    ${skill.substrates.map(s => `<span class="skill-tag">${s}</span>`).join('')}
                </div>
            </article>
        `).join('');
    }

    function filterAndRender() {
        const searchTerm = skillSearch.value.toLowerCase();
        
        const filtered = allSkills.filter(skill => {
            const matchesDomain = activeDomain === 'all' || skill.domain === activeDomain;
            const matchesSubstrate = activeSubstrate === 'all' || skill.substrates.includes(activeSubstrate);
            const matchesSearch = skill.name.toLowerCase().includes(searchTerm) || 
                                 skill.description.toLowerCase().includes(searchTerm);
            
            return matchesDomain && matchesSubstrate && matchesSearch;
        });

        renderSkills(filtered);
        updateStats(filtered.length);
    }

    function updateStats(count) {
        statsCount.textContent = `${count} skill${count !== 1 ? 's' : ''}`;
    }

    skillSearch.addEventListener('input', filterAndRender);
});
