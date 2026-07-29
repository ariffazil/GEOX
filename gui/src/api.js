const GEOX_MCP = window.location.origin + '/mcp';

export async function mcpCall(toolName, args = {}) {
  const res = await fetch(GEOX_MCP, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: crypto.randomUUID(),
      method: 'tools/call',
      params: { name: toolName, arguments: args },
    }),
  });
  const data = await res.json();
  if (data.error) {
    throw new Error(data.error.message || JSON.stringify(data.error));
  }
  return data.result;
}

export async function fetchHealth() {
  const res = await fetch(window.location.origin + '/health');
  return res.json();
}

export async function fetchToolsList() {
  const res = await fetch(GEOX_MCP, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: crypto.randomUUID(),
      method: 'tools/list',
      params: {},
    }),
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error.message);
  return data.result?.tools || [];
}
