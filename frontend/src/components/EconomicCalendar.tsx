import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { ApiError } from '../api/client';
import { type EconomicEvent, ingestCalendar, listEvents } from '../api/calendar';

/**
 * Compact economic-calendar widget for the dashboard.
 *
 * Shows medium+ impact events from a few hours ago through the next 48
 * hours. Past events are dimmed; the soonest upcoming event is bolded.
 * One click on Refresh pulls the latest from the configured adapter.
 */
export function EconomicCalendar() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['economic-calendar'],
    queryFn: () => listEvents({ hoursBack: 6, hoursAhead: 48, minImpact: 2 }),
  });

  const ingest = useMutation({
    mutationFn: () => ingestCalendar(24, 72),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['economic-calendar'] }),
  });

  // Re-evaluated each render — the event list is tiny, so memoising adds
  // nothing. `now` anchors the past/upcoming split and the "next" highlight.
  const now = Date.now();
  const next =
    (query.data ?? []).find((e) => new Date(e.ts).getTime() >= now)?.id ?? null;

  return (
    <div className="panel-pad space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-medium text-mentor-fg">Economic calendar</h2>
        <button
          type="button"
          onClick={() => ingest.mutate()}
          disabled={ingest.isPending}
          className="rounded-md border border-mentor-border bg-mentor-panelLight px-3 py-1 text-xs text-mentor-muted hover:text-mentor-fg disabled:opacity-50"
        >
          {ingest.isPending ? 'Fetching…' : 'Refresh'}
        </button>
      </div>

      {ingest.error instanceof ApiError && (
        <div className="rounded-md border border-mentor-warn/40 bg-mentor-warn/10 p-2 text-xs text-mentor-warn">
          {ingest.error.message}
        </div>
      )}

      {query.isLoading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {!query.isLoading && (query.data ?? []).length === 0 && (
        <p className="text-sm text-mentor-muted">
          No medium-or-high impact events in the window. Press <b>Refresh</b>{' '}
          once <code className="font-mono">FINNHUB_KEY</code> is set.
        </p>
      )}

      <ul className="divide-y divide-mentor-border">
        {(query.data ?? []).map((event) => (
          <Row
            key={event.id}
            event={event}
            isPast={new Date(event.ts).getTime() < now}
            isNext={event.id === next}
          />
        ))}
      </ul>
    </div>
  );
}

function Row({
  event,
  isPast,
  isNext,
}: {
  event: EconomicEvent;
  isPast: boolean;
  isNext: boolean;
}) {
  return (
    <li className={`py-2 ${isPast ? 'opacity-40' : ''}`}>
      <div className="flex items-center gap-2 text-xs">
        <ImpactBadge impact={event.impact} />
        <span className="font-mono text-mentor-muted">{event.country}</span>
        <span className={isNext ? 'font-semibold text-mentor-fg' : 'text-mentor-fg'}>
          {event.name}
        </span>
        <span className="ml-auto text-mentor-muted">
          {new Date(event.ts).toLocaleString()}
        </span>
      </div>
      {(event.forecast || event.previous || event.actual) && (
        <div className="mt-1 flex gap-3 text-xs font-mono text-mentor-muted">
          {event.previous && <span>prev {event.previous}</span>}
          {event.forecast && <span>fcst {event.forecast}</span>}
          {event.actual && (
            <span className="text-mentor-accentSoft">actual {event.actual}</span>
          )}
        </div>
      )}
    </li>
  );
}

function ImpactBadge({ impact }: { impact: number }) {
  const stars = '★'.repeat(impact) + '☆'.repeat(3 - impact);
  const tone =
    impact === 3
      ? 'text-mentor-danger'
      : impact === 2
        ? 'text-mentor-warn'
        : 'text-mentor-muted';
  return <span className={`font-mono ${tone}`}>{stars}</span>;
}
