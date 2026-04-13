/**
 * useOffsetVirtualData — generic hook for fetching paginated data
 * from any offset/limit API and caching it sparsely in memory.
 *
 * ABSTRACTION BOUNDARY: This hook knows nothing about specific endpoints
 * or response shapes. It receives a `fetchPage` adapter that the consumer
 * provides, and manages the page cache, in-flight deduplication, stale-
 * request cancellation, and end-of-list detection.
 *
 * End-of-list is detected by a "short page" — when a fetch returns fewer
 * items than `pageSize`, we know no more data exists beyond that point.
 * This works for APIs that don't return a total count.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { OffsetVirtualDataOptions, OffsetVirtualDataResult } from "./types";

export function useOffsetVirtualData<T, Q = void>(
  options: OffsetVirtualDataOptions<T, Q>,
): OffsetVirtualDataResult<T> {
  const { query, pageSize } = options;

  // Capture fetchPage in a ref so it's never a dependency that resets cache.
  const fetchPageRef = useRef(options.fetchPage);
  useEffect(() => {
    fetchPageRef.current = options.fetchPage;
  });

  // --- State ---

  const [pageCache, setPageCache] = useState<Map<number, readonly T[]>>(
    () => new Map(),
  );

  // Pages currently being fetched — ref for synchronous read/write in
  // ensureRangeLoaded, mirrored to state for render-time isLoading.
  const inFlightRef = useRef<Set<number>>(new Set());
  const [inFlightCount, setInFlightCount] = useState(0);

  const [reachedEnd, setReachedEnd] = useState(false);
  const [knownCount, setKnownCount] = useState(0);

  // --- Query change detection (render-time reset) ---
  // React docs pattern: "Adjusting state when a prop changes."
  // State resets happen during render; the abort side effect is in
  // the generation effect below.

  const [prevQuery, setPrevQuery] = useState<Q>(query);
  const [generation, setGeneration] = useState(0);

  if (JSON.stringify(prevQuery) !== JSON.stringify(query)) {
    setPrevQuery(query);
    setGeneration((g) => g + 1);
    setPageCache(new Map());
    setReachedEnd(false);
    setKnownCount(0);
    setInFlightCount(0);
  }

  // --- AbortController lifecycle ---
  // Initialized eagerly so the initial fetch (triggered below) can use
  // it immediately, before the generation effect runs. The generation
  // effect replaces it on mount (harmless — the initial controller is
  // not aborted) and on query changes (cleanup aborts stale requests).

  const abortRef = useRef(new AbortController());

  useEffect(() => {
    const controller = new AbortController();
    abortRef.current = controller;
    inFlightRef.current = new Set();
    return () => {
      controller.abort();
    };
  }, [generation]);

  // --- Fetch a single page and update cache ---

  const fetchPage = useCallback(
    (pageNum: number) => {
      const controller = abortRef.current;
      const offset = pageNum * pageSize;

      fetchPageRef.current({
        offset,
        limit: pageSize,
        query,
        signal: controller.signal,
      }).then((result) => {
        const items = result.items;
        if (controller.signal.aborted) return;

        setPageCache((prev) => {
          const next = new Map(prev);
          next.set(pageNum, items);
          return next;
        });

        inFlightRef.current.delete(pageNum);
        setInFlightCount(inFlightRef.current.size);

        const endOfPage = offset + items.length;
        setKnownCount((prev) => Math.max(prev, endOfPage));

        if (items.length < pageSize) {
          setReachedEnd(true);
        }
      }).catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        inFlightRef.current.delete(pageNum);
        setInFlightCount(inFlightRef.current.size);
        console.error(`Failed to fetch page ${pageNum}:`, err);
      });
    },
    [pageSize, query],
  );

  // --- Public API ---

  const getItem = useCallback(
    (index: number): T | undefined => {
      const pageNum = Math.floor(index / pageSize);
      const offset = index % pageSize;
      // Fresh data first, fall back to stale data from before invalidation.
      return (pageCache.get(pageNum)?.[offset]
        ?? staleCacheRef.current.get(pageNum)?.[offset]) as T | undefined;
    },
    [pageCache, pageSize],
  );

  const ensureRangeLoaded = useCallback(
    (startIndex: number, endIndex: number) => {
      if (endIndex <= startIndex) return;

      const startPage = Math.floor(startIndex / pageSize);
      const endPage = Math.floor((endIndex - 1) / pageSize);

      for (let p = startPage; p <= endPage; p++) {
        if (pageCache.has(p)) continue;
        if (inFlightRef.current.has(p)) continue;
        if (reachedEnd && p * pageSize >= knownCount) continue;

        inFlightRef.current.add(p);
        setInFlightCount(inFlightRef.current.size);
        fetchPage(p);
      }
    },
    [pageCache, pageSize, reachedEnd, knownCount, fetchPage],
  );

  // --- Initial page trigger ---
  // The hook itself kicks off the first page fetch rather than waiting
  // for VirtualList to call ensureRangeLoaded. This avoids showing
  // phantom placeholder rows before we know whether data exists.
  // (Declared after the generation effect so the AbortController is
  // ready when this runs on mount.)
  useEffect(() => {
    if (pageCache.size === 0 && !reachedEnd) {
      ensureRangeLoaded(0, pageSize);
    }
  }, [pageCache.size, reachedEnd, pageSize, ensureRangeLoaded]);

  // --- Invalidation (stale-while-revalidate) ---
  // On invalidate, we snapshot the current cache into a ref so getItem
  // can keep returning stale data while fresh pages load. This prevents
  // every card flashing to a placeholder on delete.

  const staleCacheRef = useRef<Map<number, readonly T[]>>(new Map());

  const invalidate = useCallback(() => {
    setPageCache((prev) => {
      staleCacheRef.current = prev;
      return new Map();
    });
    setGeneration((g) => g + 1);
    setReachedEnd(false);
    setKnownCount(0);
    setInFlightCount(0);
  }, []);

  // Clear stale cache once fresh data fully loads.
  if (reachedEnd && staleCacheRef.current.size > 0) {
    staleCacheRef.current = new Map();
  }

  // --- Derived values ---

  // Don't inflate totalEstimate before the first page loads. This
  // prevents VirtualList from rendering pageSize phantom placeholder
  // rows while the initial fetch is in flight.
  const hasData = pageCache.size > 0 || reachedEnd;
  const rawEstimate = reachedEnd
    ? knownCount
    : hasData
      ? knownCount + pageSize
      : 0;

  // Preserve the last non-zero estimate so totalEstimate doesn't
  // collapse to 0 during invalidation (which would flash skeleton
  // state and cause scroll jumps). Resets to 0 only when the server
  // confirms the list is truly empty (reachedEnd && knownCount === 0).
  const lastNonZeroEstimateRef = useRef(0);
  if (rawEstimate > 0) lastNonZeroEstimateRef.current = rawEstimate;

  const totalEstimate =
    rawEstimate > 0
      ? rawEstimate
      : reachedEnd && knownCount === 0
        ? 0 // truly empty — server confirmed
        : lastNonZeroEstimateRef.current;

  const isLoading = inFlightCount > 0;

  return useMemo(
    () => ({ getItem, ensureRangeLoaded, totalEstimate, isLoading, reachedEnd, invalidate }),
    [getItem, ensureRangeLoaded, totalEstimate, isLoading, reachedEnd, invalidate],
  );
}
