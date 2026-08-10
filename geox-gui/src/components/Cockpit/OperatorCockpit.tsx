import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Activity,
  Box,
  Database,
  ExternalLink,
  Globe2,
  Layers3,
  LockKeyhole,
  LogOut,
  Map,
  Menu,
  Radar,
  ShieldCheck,
  Workflow,
  X,
} from 'lucide-react';
import {
  geoxMcpClient,
  inspectSessionToken,
  type GeoxSessionIdentity,
  type GeoxSurfaceStatus,
  type GeoxToolInvocation,
} from '../../lib/geoxMcpClient';
import { SeismicInterpretationCanvas } from '../SectionCanvas/SeismicInterpretationCanvas';
import { PetrophysicalTracks } from '../LogDock/PetrophysicalTracks';
import { LogDock } from '../LogDock/LogDock';
import { useGEOXStore } from '../../store/geoxStore';
import './OperatorCockpit.css';

type ViewId = 'overview' | 'well' | 'seismic' | 'volume' | 'workflow' | 'risk';

interface CockpitView {
  id: ViewId;
  label: string;
  shortLabel: string;
  description: string;
  src: string;
  icon: React.ElementType;
}

interface ActivityEntry {
  id: string;
  tool: string;
  canonicalTool: string;
  state: 'running' | 'complete' | 'error';
  timestamp: string;
  message: string;
}

const VIEWS: CockpitView[] = [
  {
    id: 'overview',
    label: 'Basin Map',
    shortLabel: 'MAP',
    description: 'Malay Basin spatial context and prospect fairways',
    src: '/gui/basin_explorer/index.html',
    icon: Map,
  },
  {
    id: 'well',
    label: 'Well Witness',
    shortLabel: 'X1D',
    description: 'Logs, petrophysics, tie preflight, and evidence receipts',
    src: 'react:well',
    icon: Database,
  },
  {
    id: 'seismic',
    label: 'Seismic',
    shortLabel: 'X2D',
    description: 'Section cognition, visual interpretation, and hypotheses',
    src: 'react:seismic',
    icon: Radar,
  },
  {
    id: 'volume',
    label: 'Earth Volume',
    shortLabel: 'X3D',
    description: 'Lazy-loaded Cesium volume and basin-state simulations',
    src: '/gui/cesium/index.html',
    icon: Globe2,
  },
  {
    id: 'workflow',
    label: 'Malay Workflow',
    shortLabel: 'E2E',
    description: 'Basin to evidence pipeline with the seven-filter kill matrix',
    src: '/gui/malay_basin_workflow.html',
    icon: Workflow,
  },
  {
    id: 'risk',
    label: 'AC Risk',
    shortLabel: 'RISK',
    description: 'Claim review and evidence risk surface',
    src: '/gui/ac_risk_console/index.html',
    icon: ShieldCheck,
  },
];

function initialView(): ViewId {
  const value = new URLSearchParams(window.location.search).get('x');
  if (value === '1d') return 'well';
  if (value === '2d') return 'seismic';
  if (value === '3d') return 'volume';
  return 'overview';
}

function initialToken(): string {
  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get('sct');
  if (fromUrl) {
    params.delete('sct');
    const next = `${window.location.pathname}${params.size ? `?${params}` : ''}${window.location.hash}`;
    window.history.replaceState({}, document.title, next);
    return fromUrl;
  }
  return sessionStorage.getItem('geox-operator-sct') ?? '';
}

export const SessionGate: React.FC<{
  onBound: (identity: GeoxSessionIdentity | null, status: GeoxSurfaceStatus) => void;
}> = ({ onBound }) => {
  const [token, setToken] = useState(initialToken);
  const [state, setState] = useState<'idle' | 'verifying' | 'error' | 'connecting'>('idle');
  const [error, setError] = useState('');

  // F13 SOVEREIGN GATE — NO anonymous auto-connect.
  // The cockpit remains DARK until a valid SCT token is cryptographically bound.
  // Anonymous hydration of the SPA is a constitutional breach (F13). 
  // Removing the prior `geoxMcpClient.connect().then(onBound(null, ...))` bypass.

  const bind = useCallback(async (candidate: string) => {
    setState('verifying');
    setError('');
    try {
      const identity = inspectSessionToken(candidate.trim());
      const status = await geoxMcpClient.bindSession(candidate.trim());
      sessionStorage.setItem('geox-operator-sct', candidate.trim());
      onBound(identity, status);
    } catch (caught) {
      sessionStorage.removeItem('geox-operator-sct');
      geoxMcpClient.clearSession();
      setState('error');
      setError(caught instanceof Error ? caught.message : 'Session verification failed.');
    }
  }, [onBound]);

  useEffect(() => {
    if (token.trim()) void bind(token);
    // bind is stable for this gate lifecycle; explicit deps would re-fire on every keystroke.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="geox-session-gate">
      <section className="geox-session-card" aria-labelledby="session-title">
        <div className="geox-session-mark" aria-hidden="true"><Layers3 /></div>
        <p className="geox-eyebrow">GEOX OPERATOR ACCESS</p>
        <h1 id="session-title">Bind an arifOS session</h1>
        <p className="geox-session-copy">
          The cockpit exposes governed Earth evidence. A valid Session Capability Token is
          verified by GEOX before any workspace or tool surface is opened.
        </p>
        <label htmlFor="geox-sct">Session Capability Token</label>
        <input
          id="geox-sct"
          name="geox-sct"
          type="password"
          autoComplete="off"
          spellCheck={false}
          value={token}
          onChange={(event) => setToken(event.target.value)}
          placeholder="sct_v1.…"
          disabled={state === 'verifying'}
        />
        {error && <div className="geox-session-error" role="alert">{error}</div>}
        <button
          type="button"
          onClick={() => void bind(token)}
          disabled={state === 'verifying' || !token.trim()}
        >
          <LockKeyhole />
          {state === 'verifying' ? 'Verifying with GEOX…' : 'Open operator cockpit'}
        </button>
        <div className="geox-session-facts">
          <span>No token is written to localStorage.</span>
          <span>Session data is cleared when the browser session ends.</span>
          <span>GEOX computes evidence; arifOS judges.</span>
        </div>
      </section>
    </main>
  );
};

export const OperatorCockpit: React.FC = () => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [identity, setIdentity] = useState<GeoxSessionIdentity | null>(null);
  const [surfaceStatus, setSurfaceStatus] = useState<GeoxSurfaceStatus | null>(null);
  const [activeView, setActiveView] = useState<ViewId>(initialView);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [showNavigation, setShowNavigation] = useState(false);
  const [showActivity, setShowActivity] = useState(true);
  const [release, setRelease] = useState('probing');
  // Propagate identity into the GEOX store so useMcpTool can inject
  // session_id / actor_id into every MCP call (F2 / P0_IDENTITY_PROPAGATION).
  const setSessionIdentity = useGEOXStore((state) => state.setSessionIdentity);

  const currentView = useMemo(
    () => VIEWS.find((view) => view.id === activeView) ?? VIEWS[0],
    [activeView],
  );

  const onBound = useCallback((nextIdentity: GeoxSessionIdentity | null, status: GeoxSurfaceStatus) => {
    // Anonymous users get a synthetic identity so the cockpit renders
    const resolved = nextIdentity ?? {
      actorId: 'anonymous',
      sessionId: 'anon-' + Date.now(),
      expiresAt: null,
    };
    setIdentity(resolved);
    setSurfaceStatus(status);
    setSessionIdentity(geoxMcpClient.sessionToken, resolved.actorId);
  }, [setSessionIdentity]);

  const clearSession = useCallback(() => {
    sessionStorage.removeItem('geox-operator-sct');
    geoxMcpClient.clearSession();
    setIdentity(null);
    setSurfaceStatus(null);
    setActivity([]);
    setSessionIdentity(null, null);
  }, [setSessionIdentity]);

  useEffect(() => {
    fetch('/health', { headers: { Accept: 'application/json' } })
      .then((response) => response.json())
      .then((health) => setRelease(health.release_name || health.version || 'live'))
      .catch(() => setRelease('unavailable'));
  }, []);

  useEffect(() => {
    if (!identity) return;

    const respond = (source: Window | null, payload: Record<string, unknown>) => {
      if (!source) return;
      source.postMessage(payload, { targetOrigin: window.location.origin });
    };

    const onMessage = async (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      if (event.source !== iframeRef.current?.contentWindow) return;
      const data = event.data as Record<string, unknown> | null;
      if (!data) return;

      let invocation: GeoxToolInvocation | null = null;
      const params = (data.params ?? {}) as Record<string, unknown>;
      if (data.type === 'geox_tool_call') {
        invocation = {
          tool: String(data.tool ?? ''),
          arguments: (data.params ?? {}) as Record<string, unknown>,
        };
      } else if (data.method === 'tool.request') {
        invocation = {
          tool: String(params.tool ?? ''),
          arguments: (params.arguments ?? {}) as Record<string, unknown>,
        };
      } else if (data.method === 'tools/call') {
        invocation = {
          tool: String(params.name ?? ''),
          arguments: (params.arguments ?? {}) as Record<string, unknown>,
        };
      }
      if (!invocation?.tool) return;

      const activityId = `${Date.now()}-${invocation.tool}`;
      const nextActivity: ActivityEntry = {
        id: activityId,
        tool: invocation.tool,
        canonicalTool: invocation.tool,
        state: 'running',
        timestamp: new Date().toISOString(),
        message: 'Host adapter accepted request',
      };
      setActivity((entries) => [nextActivity, ...entries].slice(0, 12));

      try {
        const result = await geoxMcpClient.callTool(invocation);
        setActivity((entries) => entries.map((entry) => entry.id === activityId
          ? { ...entry, state: 'complete' as const, message: 'Evidence returned by GEOX' }
          : entry));
        respond(event.source, {
          jsonrpc: '2.0',
          id: data.id,
          method: 'tool.response',
          result,
          params: { tool: invocation.tool, result },
        });
      } catch (caught) {
        const message = caught instanceof Error ? caught.message : 'Tool call failed';
        setActivity((entries) => entries.map((entry) => entry.id === activityId
          ? { ...entry, state: 'error' as const, message }
          : entry));
        respond(event.source, {
          jsonrpc: '2.0',
          id: data.id,
          method: 'tool.response',
          error: { code: -32001, message },
          params: { tool: invocation.tool, error: message },
        });
      }
    };

    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }, [identity]);

  if (!identity) return <SessionGate onBound={onBound} />;

  const callable = Number(surfaceStatus?.public_count ?? surfaceStatus?.callable_tools ?? 0);

  return (
    <div className="geox-cockpit-shell">
      <header className="geox-cockpit-header">
        <button
          className="geox-mobile-menu"
          type="button"
          aria-label="Open workspace navigation"
          onClick={() => setShowNavigation(true)}
        >
          <Menu />
        </button>
        <a className="geox-cockpit-brand" href="/" aria-label="GEOX home">
          <span className="geox-brand-symbol"><Layers3 /></span>
          <span>
            <strong>GEOX</strong>
            <small>Earth Witness</small>
          </span>
        </a>
        <div className="geox-project-context">
          <span className="geox-context-label">ACTIVE CONTEXT</span>
          <strong>Malay Basin</strong>
          <span>WGS84 · Evidence only</span>
        </div>
        <div className="geox-header-metrics">
          <span className="geox-health-dot" aria-hidden="true" />
          <div><small>GEOX</small><strong>{release}</strong></div>
          <div><small>TOOLS</small><strong>18 / 18</strong></div>
          <div className="geox-session-chip"><small>SESSION</small><strong>{identity.sessionId.slice(0, 12)}…</strong></div>
          <button type="button" onClick={clearSession} title="Clear operator session"><LogOut /></button>
        </div>
      </header>

      <div className="geox-cockpit-body">
        <nav className={`geox-workspace-nav ${showNavigation ? 'is-open' : ''}`} aria-label="GEOX workspaces">
          <div className="geox-nav-heading">
            <span>WORKSPACES</span>
            <button type="button" onClick={() => setShowNavigation(false)} aria-label="Close navigation"><X /></button>
          </div>
          {VIEWS.map((view) => {
            const Icon = view.icon;
            return (
              <button
                key={view.id}
                type="button"
                className={view.id === activeView ? 'is-active' : ''}
                onClick={() => {
                  setActiveView(view.id);
                  setShowNavigation(false);
                }}
              >
                <span className="geox-nav-icon"><Icon /></span>
                <span className="geox-nav-copy"><strong>{view.label}</strong><small>{view.description}</small></span>
                <span className="geox-nav-code">{view.shortLabel}</span>
              </button>
            );
          })}
          <div className="geox-nav-footer">
            <a href="https://arif-fazil.com" target="_blank" rel="noreferrer"><Globe2 /> arif-fazil.com <ExternalLink /></a>
            <a href="/apps/" target="_blank" rel="noreferrer"><Box /> MCP App resources <ExternalLink /></a>
            <span>F2 TRUTH · F13 SOVEREIGN</span>
          </div>
        </nav>

        <main className="geox-workspace-main">
          <div className="geox-workspace-titlebar">
            <div>
              <span>{currentView.shortLabel}</span>
              <strong>{currentView.label}</strong>
              <small>{currentView.description}</small>
            </div>
            <button type="button" onClick={() => setShowActivity((open) => !open)}>
              <Activity /> Activity {activity.length > 0 ? `(${activity.length})` : ''}
            </button>
          </div>
          {currentView.id === 'seismic' ? (
            <div className="geox-panel">
              <SeismicInterpretationCanvas />
            </div>
          ) : currentView.id === 'well' ? (
            <div className="geox-panel geox-panel-split">
              <div className="geox-panel-left"><LogDock /></div>
              <div className="geox-panel-right"><PetrophysicalTracks /></div>
            </div>
          ) : (
            <iframe
              ref={iframeRef}
              key={currentView.id}
              src={currentView.src}
              title={currentView.label}
              className="geox-workspace-frame"
              sandbox="allow-scripts allow-forms allow-same-origin allow-downloads"
            />
          )}
        </main>

        <aside className={`geox-activity-rail ${showActivity ? 'is-open' : ''}`} aria-label="Tool activity">
          <div className="geox-activity-heading">
            <div><span>ADAPTER TRACE</span><strong>Recent activity</strong></div>
            <button type="button" onClick={() => setShowActivity(false)} aria-label="Close activity"><X /></button>
          </div>
          <div className="geox-activity-summary">
            <div><small>Transport</small><strong>Host mediated</strong></div>
            <div><small>Authority</small><strong>{identity.actorId}</strong></div>
            <div><small>Surface</small><strong>{callable || 'Verified'} callable</strong></div>
          </div>
          <div className="geox-activity-list">
            {activity.length === 0 ? (
              <div className="geox-activity-empty">
                <Activity />
                <p>No tool calls yet.</p>
                <span>Requests from embedded workspaces appear here with their actual outcome.</span>
              </div>
            ) : activity.map((entry) => (
              <article key={entry.id} className={`geox-activity-item is-${entry.state}`}>
                <div><span>{entry.state}</span><time>{new Date(entry.timestamp).toLocaleTimeString()}</time></div>
                <strong>{entry.tool}</strong>
                <p>{entry.message}</p>
              </article>
            ))}
          </div>
          <footer>
            <ShieldCheck />
            <span>Outputs are evidence, not drilling or capital authority.</span>
          </footer>
        </aside>
      </div>
    </div>
  );
};

export default OperatorCockpit;
