/**
 * GEOX A2A Gateway
 * Agent-to-Agent coordination service
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3002;

// Load agent cards
const AGENTS_DIR = process.env.AGENTS_DIR || path.join(__dirname, 'agents');
const agentCards = new Map();

function loadAgentCards() {
  const domains = fs.readdirSync(AGENTS_DIR);
  for (const domain of domains) {
    const cardPath = path.join(AGENTS_DIR, domain, 'agent-card.json');
    if (fs.existsSync(cardPath)) {
      const card = JSON.parse(fs.readFileSync(cardPath, 'utf8'));
      agentCards.set(card.name, card);
    }
  }
  console.log(`Loaded ${agentCards.size} agent cards`);
}

loadAgentCards();

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['https://geox.arif-fazil.com']
}));
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    agents: agentCards.size,
    version: '2026.04.11'
  });
});

// List all agents (A2A discovery)
app.get('/agents', (req, res) => {
  const agents = Array.from(agentCards.values()).map(card => ({
    name: card.name,
    description: card.description,
    url: card.url,
    version: card.version,
    capabilities: card.capabilities,
    skills: card.skills.map(s => s.id),
    _geox: card._geox
  }));
  res.json({ agents });
});

// Get specific agent card
app.get('/agents/:name/card.json', (req, res) => {
  const card = agentCards.get(req.params.name);
  if (!card) {
    return res.status(404).json({ error: 'Agent not found' });
  }
  res.json(card);
});

// A2A Task submission
app.post('/tasks/send', async (req, res) => {
  const { sessionId, message, metadata = {} } = req.body;
  
  const task = {
    id: uuidv4(),
    sessionId: sessionId || uuidv4(),
    status: 'submitted',
    createdAt: new Date().toISOString(),
    message,
    metadata: {
      ...metadata,
      delegation_chain: [req.headers['x-agent-id'] || 'anonymous', ...metadata.delegation_chain || []]
    }
  };
  
  // Route to appropriate agent based on skill_id in metadata
  const skillId = metadata.skill_id;
  const targetAgent = findAgentForSkill(skillId);
  
  if (!targetAgent) {
    task.status = 'failed';
    task.error = `No agent available for skill: ${skillId}`;
    return res.status(422).json(task);
  }
  
  // Simulate task execution
  task.status = 'working';
  
  // Add GEOX telemetry
  task._geox_telemetry = {
    epoch: new Date().toISOString(),
    capability_id: skillId,
    surface: 'a2a',
    dS: 0.03,
    peace2: 1.02,
    kappa_r: 0.18,
    confidence: 0.85,
    verdict: '888_QUALIFY',
    witness: { human: true, ai: true, earth: false },
    qdf: 'evidence-linked'
  };
  
  res.json(task);
});

// Task status
app.get('/tasks/:id', (req, res) => {
  // In production, this would look up actual task state
  res.json({
    id: req.params.id,
    status: 'working',
    updatedAt: new Date().toISOString()
  });
});

// Cancel task
app.post('/tasks/:id/cancel', (req, res) => {
  res.json({
    id: req.params.id,
    status: 'canceled',
    canceledAt: new Date().toISOString()
  });
});

// Utility: Find agent that can handle a skill
function findAgentForSkill(skillId) {
  for (const [name, card] of agentCards) {
    if (card.skills.some(s => s.id === skillId)) {
      return name;
    }
  }
  return null;
}

// Well-known agent directory
app.get('/.well-known/agents.json', (req, res) => {
  const directory = Array.from(agentCards.values()).map(card => ({
    name: card.name,
    url: card.url,
    capabilities: card.capabilities
  }));
  res.json({ directory });
});

app.listen(PORT, () => {
  console.log(`GEOX A2A Gateway running on port ${PORT}`);
  console.log(`Agents: ${Array.from(agentCards.keys()).join(', ')}`);
});
