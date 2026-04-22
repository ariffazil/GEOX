/**
 * MCPBridge.js — postMessage Event Handler
 * =========================================
 * Wires WellDesk app ↔ MCP host via postMessage protocol.
 * Handles all event types defined in well_desk_event_schema.json
 */

class MCPBridge {
  constructor() {
    this.hostOrigin = "*";  // Restrict in production
    this.requestQueue = new Map();
    this.callbacks = {
      onInitialize: null,
      onToolResult: null,
      onPhysicsResult: null,
      onVaultSeal: null,
      onError: null
    };
    this.isMcpMode = false;
    this._bindListener();
  }

  /**
   * Register callback handlers
   */
  on(event, handler) {
    if (this.callbacks[`on${event.charAt(0).toUpperCase() + event.slice(1)}`] !== undefined) {
      this.callbacks[`on${event.charAt(0).toUpperCase() + event.slice(1)}`] = handler;
    }
  }

  // ── Event Listener ────────────────────────────────────────────────────────

  _bindListener() {
    window.addEventListener("message", (event) => {
      // Validate origin in production
      // if (event.origin !== this.hostOrigin) return;

      const msg = event.data;
      if (!msg || !msg.type) return;

      switch (msg.type) {
        case "app.initialize":
          this._handleInitialize(msg.payload);
          break;
        case "tool.result":
          this._handleToolResult(msg.payload);
          break;
        case "physics.result":
          this._handlePhysicsResult(msg.payload);
          break;
        case "vault.seal":
          this._handleVaultSeal(msg.payload);
          break;
        case "app.error":
          this._handleError(msg.payload);
          break;
      }
    });

    // Notify host that app is ready
    this._post("app.ready", { appId: "geox.subsurface.well-desk" });
  }

  // ── Incoming Handlers ─────────────────────────────────────────────────────

  _handleInitialize(payload) {
    this.isMcpMode = true;
    if (this.callbacks.onInitialize) {
      this.callbacks.onInitialize(payload);
    }
  }

  _handleToolResult(payload) {
    const { request_id, result, vault_receipt, physics9_state } = payload;

    // Resolve queued request
    if (request_id && this.requestQueue.has(request_id)) {
      const { resolve } = this.requestQueue.get(request_id);
      this.requestQueue.delete(request_id);
      resolve({ result, vault_receipt, physics9_state });
    }

    if (this.callbacks.onToolResult) {
      this.callbacks.onToolResult(result, vault_receipt, physics9_state);
    }
  }

  _handlePhysicsResult(payload) {
    if (this.callbacks.onPhysicsResult) {
      this.callbacks.onPhysicsResult(payload.physics9_state, payload.integrity_score, payload.grade);
    }
  }

  _handleVaultSeal(payload) {
    if (this.callbacks.onVaultSeal) {
      this.callbacks.onVaultSeal(payload.receipt_id, payload.status, payload.timestamp);
    }
  }

  _handleError(payload) {
    if (this.callbacks.onError) {
      this.callbacks.onError(payload.error, payload.code);
    }
  }

  // ── Outgoing Messages ─────────────────────────────────────────────────────

  _post(type, payload) {
    if (window.parent !== window) {
      window.parent.postMessage({ type, payload, appId: "geox.subsurface.well-desk" }, this.hostOrigin);
    }
  }

  /**
   * Request tool execution from MCP host
   */
  async requestTool(toolName, params) {
    const requestId = `wd-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.requestQueue.delete(requestId);
        reject(new Error(`Tool request timeout: ${toolName}`));
      }, 30000);

      this.requestQueue.set(requestId, {
        resolve: (result) => {
          clearTimeout(timeout);
          resolve(result);
        },
        reject: (err) => {
          clearTimeout(timeout);
          reject(err);
        }
      });

      this._post("tool.request", {
        tool_name: toolName,
        params,
        request_id: requestId
      });
    });
  }

  /**
   * Send UI action to host (forward/inverse/metabolic trigger)
   */
  sendAction(actionType, params) {
    this._post("ui.action", { action_type: actionType, params });
  }

  /**
   * Sync state to host
   */
  syncState(wellId, physics9State, depthRange, activeTracks) {
    this._post("app.state.sync", {
      well_id: wellId,
      physics9_state: physics9State,
      depth_range: depthRange,
      active_tracks: activeTracks
    });
  }

  /**
   * Launch well-desk via MCP tool
   */
  async launchWellDesk(wellId, mode = "1d", lasUrl = null, physicsParams = null) {
    return this.requestTool("geox_well_desk_launch", {
      well_id: wellId,
      mode,
      las_url: lasUrl,
      physics_params: physicsParams
    });
  }

  /**
   * Run forward physics computation
   */
  async runForward(wellId, porosity, sw, vsh, fluidType) {
    return this.launchWellDesk(wellId, "forward", null, {
      porosity, sw, vsh, fluid_type: fluidType
    });
  }

  /**
   * Run inverse physics computation
   */
  async runInverse(wellId, vpObs, vsObs, rhoObs) {
    return this.launchWellDesk(wellId, "inverse", null, {
      observed_vp: vpObs,
      observed_vs: vsObs,
      observed_rho: rhoObs
    });
  }

  /**
   * Run metabolic convergence
   */
  async runMetabolic(wellId, observedVp, observedAi) {
    return this.launchWellDesk(wellId, "metabolic", null, {
      observed_vp: observedVp,
      observed_ai: observedAi
    });
  }

  /**
   * Check if running inside MCP host
   */
  isMCP() {
    return this.isMcpMode || window.self !== window.top;
  }
}
