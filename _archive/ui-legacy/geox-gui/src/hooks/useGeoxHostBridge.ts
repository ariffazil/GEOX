/**
 * GEOX Host Bridge Hook — DITEMPA BUKAN DIBERI
 * 
 * React hook for the GEOX Dashboard (Host) to manage communication
 * with embedded Microfrontends (Apps) via postMessage.
 */

import { useEffect, useCallback } from 'react';
import type { RefObject } from 'react';
import { useGEOXStore } from '../store/geoxStore';
import type { 
  GeoxEvent, 
  GeoxMethod,
} from '../types';

export function useGeoxHostBridge(iframeRef: RefObject<HTMLIFrameElement>) {
  const store = useGEOXStore();

  const sendToApp = useCallback((method: GeoxMethod, params: any, id?: string | number) => {
    if (!iframeRef.current?.contentWindow) return;

    const event: GeoxEvent = {
      jsonrpc: '2.0',
      method,
      params,
      id: id || Math.random().toString(36).substring(7),
      timestamp: new Date().toISOString(),
    };

    console.log(`[GEOX Host] Sending to App: ${method}`, event);
    iframeRef.current.contentWindow.postMessage(event, '*');
  }, [iframeRef]);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Basic JSON-RPC validation
      const data = event.data as GeoxEvent;
      if (!data || data.jsonrpc !== '2.0') return;

      // Ensure message comes from our iframe
      if (event.source !== iframeRef.current?.contentWindow) return;

      console.log(`[GEOX Host] Received from App: ${data.method}`, data);

      switch (data.method) {
        case 'app.initialize': {
          console.log('[GEOX Host] App Handshake:', data.params.app_id);
          store.setGEOXConnected(true);
          store.updateFloorStatus('F11', 'green', `App ${data.params.app_id} initialized`);
          
          // Send initial context back to app
          sendToApp('app.context.patch', {
            coordinates: store.selectedCoordinate,
            well_id: store.selectedWell,
            prospect_id: store.selectedProspect
          });
          break;
        }

        case 'ui.action': {
          console.log('[GEOX Host] UI Action from App:', data.params.action);
          // Update store or trigger host-side logic
          break;
        }

        case 'ui.state.sync': {
          console.log('[GEOX Host] State Sync from App:', data.params);
          // Sync app state to host store if needed
          break;
        }

        case 'tool.request': {
          const { tool, arguments: args } = data.params;
          console.log(`[GEOX Host] Tool Request: ${tool}`, args);
          // Forward to MCP client and return result via tool.result
          store.executeToolRequest(tool, args).then(result => {
            sendToApp('tool.result', {
              tool,
              result,
              requestId: data.id,
            });
          }).catch(error => {
            sendToApp('tool.result', {
              tool,
              error: String(error),
              requestId: data.id,
            });
          });
          break;
        }

        case 'tool.cancelled': {
          console.log('[GEOX Host] Tool Cancelled:', data.params);
          // Propagate cancellation to any in-flight tool execution
          store.cancelToolExecution(data.params?.requestId);
          break;
        }

        default:
          console.warn(`[GEOX Host] Unhandled method: ${data.method}`);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [iframeRef, store, sendToApp]);

  return {
    sendToApp,
    // MCP-UI bidirectional notification helpers (SEP-1865)
    sendToolInput: (tool: string, input: Record<string, unknown>, requestId?: string) => {
      sendToApp('tool.input' as GeoxMethod, { tool, input }, requestId);
    },
    sendToolResult: (tool: string, result: unknown, requestId?: string) => {
      sendToApp('tool.result' as GeoxMethod, { tool, result }, requestId);
    },
    sendToolCancelled: (requestId?: string) => {
      sendToApp('tool.cancelled' as GeoxMethod, { requestId });
    },
  };
}
