/**
 * useEventStreamData — hook that connects to an SSE event stream,
 * accumulates events, groups contiguous same-source events, and
 * exposes the result as OffsetVirtualDataResult so VirtualList
 * can consume it directly.
 *
 * Unlike useOffsetVirtualData (offset/limit pagination), this hook
 * is designed for append-only streams consumed via EventSource.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Event } from "../../api/events";
import { EVENTS_STREAM_URL } from "../../api/events";
import type { OffsetVirtualDataResult } from "./types";

export type EventGroup = {
  /** Full dispatch UUID (source_id). */
  sourceId: string;
  /** First 8 characters of sourceId for display. */
  shortId: string;
  /** Raw events in this group. */
  events: Event[];
  /** ID of the first event — used as a stable React key. */
  firstEventId: number;
};

export function useEventStreamData(): OffsetVirtualDataResult<EventGroup> {
  const [groups, setGroups] = useState<EventGroup[]>([]);
  const [connected, setConnected] = useState(false);
  const groupsRef = useRef<EventGroup[]>([]);
  const lastSeenIdRef = useRef(0);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback((since: number) => {
    // Close any existing connection.
    eventSourceRef.current?.close();

    const url = `${EVENTS_STREAM_URL}?since=${since}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      setConnected(true);
    };

    es.onmessage = (msg) => {
      const event: Event = JSON.parse(msg.data);
      lastSeenIdRef.current = event.id;

      const current = groupsRef.current;
      const lastGroup = current.length > 0 ? current[current.length - 1] : null;

      if (lastGroup && lastGroup.sourceId === event.source_id) {
        // Append to existing group — create a new array reference for the
        // group so React sees the change.
        const updatedGroup: EventGroup = {
          ...lastGroup,
          events: [...lastGroup.events, event],
        };
        const next = [...current.slice(0, -1), updatedGroup];
        groupsRef.current = next;
        setGroups(next);
      } else {
        // New group.
        const newGroup: EventGroup = {
          sourceId: event.source_id,
          shortId: event.source_id.slice(0, 8),
          events: [event],
          firstEventId: event.id,
        };
        const next = [...current, newGroup];
        groupsRef.current = next;
        setGroups(next);
      }
    };

    es.onerror = () => {
      setConnected(false);
      // EventSource will auto-reconnect, but it restarts from the
      // beginning of the stream. Close and reconnect with our cursor
      // so we don't receive duplicates.
      es.close();
      setTimeout(() => {
        connect(lastSeenIdRef.current);
      }, 2000);
    };
  }, []);

  useEffect(() => {
    connect(0);
    return () => {
      eventSourceRef.current?.close();
      eventSourceRef.current = null;
    };
  }, [connect]);

  // --- OffsetVirtualDataResult interface ---

  const getItem = useCallback(
    (index: number): EventGroup | undefined => groups[index],
    [groups],
  );

  const ensureRangeLoaded = useCallback(() => {
    // No-op — all data is already in memory from the SSE stream.
  }, []);

  const invalidate = useCallback(() => {
    groupsRef.current = [];
    lastSeenIdRef.current = 0;
    setGroups([]);
    connect(0);
  }, [connect]);

  return useMemo(
    () => ({
      getItem,
      ensureRangeLoaded,
      totalEstimate: groups.length,
      isLoading: !connected && groups.length === 0,
      reachedEnd: false,
      invalidate,
    }),
    [getItem, ensureRangeLoaded, groups.length, connected, invalidate],
  );
}
