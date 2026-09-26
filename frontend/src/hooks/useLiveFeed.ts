import { useState, useEffect, useRef } from 'react';

export interface LiveActivity {
  id: string;
  type: string;
  title: string;
  subtitle: string;
  timestamp: string;
  badgeColor: string;
}

export function useLiveFeed(onEventReceived?: (type: string, data: any) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [activities, setActivities] = useState<LiveActivity[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const url = '/api/events/live';
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
      console.log('[SSE] Connected to live event stream');
    };

    es.onerror = () => {
      setIsConnected(false);
    };

    // Generic Event Listener
    const handleEvent = (type: string, event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log(`[SSE] ${type}:`, data);

        let activity: LiveActivity | null = null;
        const now = new Date().toLocaleTimeString();

        if (type === 'agent_decision') {
          activity = {
            id: Math.random().toString(),
            type: 'decision',
            title: `AI Action: ${data.decision_type.replace('_', ' ').toUpperCase()}`,
            subtitle: data.reasoning,
            timestamp: now,
            badgeColor: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
          };
        } else if (type === 'webhook_event') {
          const sent = data.sentiment ? ` (${data.sentiment} sentiment)` : '';
          activity = {
            id: Math.random().toString(),
            type: 'event',
            title: `Telemetry: ${data.event_type.toUpperCase()}${sent}`,
            subtitle: data.payload?.text || `Event recorded for contact ${data.contact_id || 'prospect'}`,
            timestamp: now,
            badgeColor: data.sentiment === 'positive' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
          };
        } else if (type === 'approval_created') {
          activity = {
            id: Math.random().toString(),
            type: 'approval',
            title: `HITL Gate: ${data.type.replace('_', ' ').toUpperCase()}`,
            subtitle: 'Human signoff required before autonomous execution',
            timestamp: now,
            badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30'
          };
        }

        if (activity) {
          setActivities(prev => [activity!, ...prev.slice(0, 19)]);
        }

        if (onEventReceived) {
          onEventReceived(type, data);
        }
      } catch (err) {
        console.error('[SSE] Parse error:', err);
      }
    };

    es.addEventListener('agent_decision', (e) => handleEvent('agent_decision', e));
    es.addEventListener('webhook_event', (e) => handleEvent('webhook_event', e));
    es.addEventListener('approval_created', (e) => handleEvent('approval_created', e));
    es.addEventListener('approval_resolved', (e) => handleEvent('approval_resolved', e));
    es.addEventListener('contacts_discovered', (e) => handleEvent('contacts_discovered', e));

    return () => {
      es.close();
      setIsConnected(false);
    };
  }, []);

  return { isConnected, activities };
}
