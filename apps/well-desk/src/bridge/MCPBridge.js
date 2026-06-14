/**
 * MCP Bridge — WellDesk ↔ AAA Host
 * ==================================
 * Secure postMessage listener with JSON-RPC 2.0 validation.
 * Implements SEP-1865 ext-apps View protocol (stable 2026-01-26).
 *
 * Protocol flow:
 *   1. View sends ui/initialize
 *   2. Host replies with protocolVersion, hostCapabilities, hostContext
 *   3. View sends ui/notifications/initialized
 *   4. Host sends ui/notifications/tool-input (arguments)
 *   5. Host sends ui/notifications/tool-result (envelope)
 *   6. View may send tools/call, resources/read, ui/update-model-context
 *   7. Host may send ui/notifications/host-context-changed, ping
 *
 * Governance:
 *   - holds[] in envelope → 888 HOLD banner
 *   - constraints.veto.active === true → F13 VETO banner
 *   - policyState === "review_required" → amber review state
 *   - policyState === "observe" → read-only mode
 *
 * DITEMPA BUKAN DIBERI
 */
(function () {
  'use strict';

  const PROTOCOL_VERSION = '2026-01-26';
  const APP_NAME = 'geox-well-desk';
  const APP_VERSION = '1.0.0';
  const TIMEOUT_MS = 15000;

  // ── State ──────────────────────────────────────────────────────────────
  const state = {
    initialized: false,
    hostReady: false,
    standalone: window.parent === window,
    nextId: 1,
    pending: new Map(),
    hostContext: null,
    toolInput: null,
    toolResult: null,
    modelContext: null,
  };

  // ── DOM refs (injected after bridge loads) ────────────────────────────
  let el = {};

  function cacheDom() {
    el.status = document.getElementById('mcpStatus');
    el.error = document.getElementById('mcpError');
    el.holdBanner = document.getElementById('holdBanner');
    el.vetoBanner = document.getElementById('vetoBanner');
    el.promoteBtn = document.getElementById('promoteInterpretation');
  }

  // ── Validation ────────────────────────────────────────────────────────
  function isPlainObject(v) {
    return v !== null && typeof v === 'object' && !Array.isArray(v);
  }

  function isJsonRpcMessage(msg) {
    return isPlainObject(msg) && msg.jsonrpc === '2.0';
  }

  /** Safe parse: string → object, reject non-JSON-RPC-2.0 */
  function safeParseMessage(event) {
    let data = event.data;
    if (typeof data === 'string') {
      try { data = JSON.parse(data); }
      catch { return null; }
    }
    return isJsonRpcMessage(data) ? data : null;
  }

  /** Whitelist of methods the View is allowed to receive */
  const ALLOWED_METHODS = new Set([
    'ui/notifications/tool-input',
    'ui/notifications/tool-input-partial',
    'ui/notifications/tool-result',
    'ui/notifications/tool-cancelled',
    'ui/notifications/host-context-changed',
    'ui/resource-teardown',
    'ping',
  ]);

  // ── Messaging ─────────────────────────────────────────────────────────
  function sendRequest(method, params) {
    if (state.standalone) {
      return Promise.reject(new Error('No MCP host available'));
    }
    const id = state.nextId++;
    const payload = { jsonrpc: '2.0', id, method, params };
    return new Promise((resolve, reject) => {
      state.pending.set(id, { resolve, reject, method, ts: Date.now() });
      window.parent.postMessage(payload, '*');
      setTimeout(() => {
        if (state.pending.has(id)) {
          state.pending.delete(id);
          reject(new Error(`Timeout: ${method} (${TIMEOUT_MS}ms)`));
        }
      }, TIMEOUT_MS);
    });
  }

  function sendNotification(method, params) {
    if (state.standalone) return;
    window.parent.postMessage({ jsonrpc: '2.0', method, params }, '*');
  }

  function sendResponse(id, result) {
    if (state.standalone || id == null) return;
    window.parent.postMessage({ jsonrpc: '2.0', id, result }, '*');
  }

  // ── Response correlation ─────────────────────────────────────────────
  function handleRpcResponse(msg) {
    const pending = state.pending.get(msg.id);
    if (!pending) return;
    state.pending.delete(msg.id);
    if (msg.error) {
      pending.reject(new Error(msg.error.message || 'RPC error'));
      return;
    }
    pending.resolve(msg.result);
  }

  // ── Governance renderers ──────────────────────────────────────────────
  function renderGovernance(envelope) {
    const holds = Array.isArray(envelope?.holds) ? envelope.holds : [];
    const constraints = isPlainObject(envelope?.constraints)
      ? envelope.constraints
      : { policyState: 'observe', disabledActions: [], veto: { active: false } };

    // 888 HOLD banner
    if (el.holdBanner) {
      const blocking = holds.filter(h => h.blocking !== false);
      el.holdBanner.hidden = blocking.length === 0;
      if (blocking.length > 0) {
        el.holdBanner.textContent = '888 HOLD — '
          + blocking.map(h => h.reason || h.code || 'review required').join(' | ');
        el.holdBanner.style.display = 'block';
      } else {
        el.holdBanner.style.display = 'none';
      }
    }

    // F13 VETO banner
    if (el.vetoBanner) {
      const veto = constraints.veto?.active === true;
      el.vetoBanner.hidden = !veto;
      el.vetoBanner.textContent = veto
        ? 'F13 VETO — human block active'
        : '';
      el.vetoBanner.style.display = veto ? 'block' : 'none';
    }

    // Disable commit actions under veto or hold
    const disabled = constraints.disabledActions || [];
    const isFrozen = constraints.veto?.active === true
      || holds.some(h => h.blocking !== false);
    if (el.promoteBtn) {
      el.promoteBtn.disabled = isFrozen || disabled.includes('geox_claim_create');
    }
  }

  function renderViewModel(viewModel) {
    window.WELLDESK_VIEWMODEL = viewModel;
    // Dispatch custom event for existing render pipeline
    window.dispatchEvent(new CustomEvent('well-desk:viewmodel', {
      detail: { viewModel },
    }));
  }

  // ── Tool result handler ──────────────────────────────────────────────
  function handleToolResult(result) {
    state.toolResult = result;
    const structured = result?.structuredContent || {};
    const envelope = structured?.envelope || structured;

    if (envelope?.viewModel) renderViewModel(envelope.viewModel);
    renderGovernance(envelope);

    setStatus(envelope?.constraints?.policyState === 'veto' ? 'VETO'
      : envelope?.holds?.length ? 'HOLD'
      : 'CONNECTED');
  }

  // ── Method dispatcher (whitelisted) ──────────────────────────────────
  function handleMethod(msg) {
    switch (msg.method) {
      case 'ui/notifications/tool-input-partial':
      case 'ui/notifications/tool-input':
        state.toolInput = msg.params?.arguments || null;
        break;

      case 'ui/notifications/tool-result':
        handleToolResult(msg.params);
        break;

      case 'ui/notifications/tool-cancelled':
        setError(msg.params?.reason || 'Tool cancelled');
        break;

      case 'ui/notifications/host-context-changed':
        state.hostContext = {
          ...(state.hostContext || {}),
          ...(msg.params || {}),
        };
        break;

      case 'ui/resource-teardown': {
        sendResponse(msg.id, {});
        teardown(msg.params?.reason || 'resource teardown');
        break;
      }

      case 'ping':
        sendResponse(msg.id, {});
        break;
    }
  }

  // ── Status helpers ───────────────────────────────────────────────────
  function setStatus(text) {
    if (el.status) el.status.textContent = text;
  }
  function setError(text) {
    if (el.error) el.error.textContent = text || '';
  }

  function teardown(reason) {
    setStatus('TEARDOWN: ' + reason);
    state.initialized = false;
  }

  // ── Standalone bootstrap ─────────────────────────────────────────────
  function bootstrapStandalone() {
    const mockEnvelope = {
      summary: 'Standalone preview — no MCP host',
      viewModel: null,
      holds: [],
      constraints: {
        policyState: 'observe',
        disabledActions: [],
        veto: { active: false, reason: null, authority: null },
      },
    };
    renderGovernance(mockEnvelope);
    window.WELLDESK_MCP_BRIDGE = bridge;
  }

  // ── Initialization ───────────────────────────────────────────────────
  async function initialize() {
    cacheDom();

    if (state.standalone) {
      setStatus('STANDALONE');
      bootstrapStandalone();
      return;
    }

    setStatus('INITIALIZING');
    try {
      const result = await sendRequest('ui/initialize', {
        protocolVersion: PROTOCOL_VERSION,
        clientInfo: { name: APP_NAME, version: APP_VERSION },
        capabilities: {},
        appCapabilities: {
          availableDisplayModes: ['inline', 'fullscreen'],
        },
      });

      state.initialized = true;
      state.hostContext = result?.hostContext || null;
      sendNotification('ui/notifications/initialized', {});
      setStatus('READY');
    } catch (err) {
      setError(err.message || String(err));
      setStatus('INIT_FAILED');
    }
  }

  // ── postMessage listener (secure) ────────────────────────────────────
  window.addEventListener('message', function onMessage(event) {
    const msg = safeParseMessage(event);
    if (!msg) return;

    // Response correlation: has id + result|error
    if (msg.id != null && (msg.result !== undefined || msg.error !== undefined)) {
      handleRpcResponse(msg);
      return;
    }

    // Outbound method: must be whitelisted
    if (!ALLOWED_METHODS.has(msg.method)) return;

    handleMethod(msg);
  });

  // ── Public API (exposed for JS console and existing render pipeline) ─
  const bridge = {
    /** Request a server tool call through the host */
    requestTool(name, args) {
      return sendRequest('tools/call', { name, arguments: args });
    },
    /** Update the shared model context */
    updateModelContext(structuredContent) {
      return sendRequest('ui/update-model-context', { structuredContent });
    },
    /** Read an MCP resource through the host */
    readResource(uri) {
      return sendRequest('resources/read', { uri });
    },
    /** Get current host context */
    getHostContext() {
      return state.hostContext;
    },
    /** Get latest tool result envelope */
    getLastEnvelope() {
      return state.toolResult?.structuredContent?.envelope || null;
    },
    /** Expose state for debugging */
    _state: state,
  };

  // ── Wire promote button ─────────────────────────────────────────────
  function wireActions() {
    if (el.promoteBtn) {
      el.promoteBtn.addEventListener('click', async () => {
        setError('');
        const vm = window.WELLDESK_VIEWMODEL;
        try {
          const result = await bridge.requestTool('geox_claim_create', {
            wellId: vm?.wellId || 'unknown',
          });
          handleToolResult(result);
        } catch (err) {
          setError(err.message || String(err));
        }
      });
    }
  }

  // ── Boot ─────────────────────────────────────────────────────────────
  // Delay boot slightly to ensure DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      wireActions();
      initialize();
    });
  } else {
    wireActions();
    initialize();
  }

  // Expose bridge globally for legacy code
  window.WELLDESK_MCP_BRIDGE = bridge;

})();
