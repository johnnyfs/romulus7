/**
 * Types for the reusable offset/limit virtualization layer.
 *
 * ABSTRACTION BOUNDARY: Nothing in this directory references any specific
 * backend resource (workspaces, users, etc.). The generic parameters T
 * (item type) and Q (query/filter type) are filled in by each consumer.
 */

/**
 * A single page of results returned by a fetchPage adapter.
 * The consumer's adapter must normalize its API response into this shape.
 */
export type PageResult<T> = {
  readonly items: readonly T[];
};

/**
 * A function that fetches one page of data.
 *
 * T = item type, Q = query/filter type (use `void` for no query).
 * The hook calls this with offset, limit, the current query value,
 * and an AbortSignal so in-flight requests can be cancelled when
 * the query changes or the component unmounts.
 */
export type FetchPageFn<T, Q> = (params: {
  offset: number;
  limit: number;
  query: Q;
  signal: AbortSignal;
}) => Promise<PageResult<T>>;

/**
 * Configuration accepted by useOffsetVirtualData.
 */
export type OffsetVirtualDataOptions<T, Q> = {
  /** Current query/filter value. Cache resets when this changes (by value). */
  query: Q;
  /** Adapter function that fetches a single page from the API. */
  fetchPage: FetchPageFn<T, Q>;
  /** Number of items per page — must match the backend's limit. */
  pageSize: number;
};

/**
 * The object returned by useOffsetVirtualData.
 * VirtualList reads this to decide what to render.
 */
export type OffsetVirtualDataResult<T> = {
  /** Get the item at an absolute index, or undefined if not yet loaded. */
  getItem: (index: number) => T | undefined;

  /**
   * Ensure items in [startIndex, endIndex) are loaded.
   * The hook figures out which pages cover this range and fetches any
   * that are not already cached or in-flight.
   */
  ensureRangeLoaded: (startIndex: number, endIndex: number) => void;

  /**
   * Best-known total item count. Grows as pages are discovered.
   * Becomes exact once a short page is received (items < pageSize).
   */
  totalEstimate: number;

  /** True while at least one page fetch is in progress. */
  isLoading: boolean;

  /** True once a short page confirms we've seen the entire list. */
  reachedEnd: boolean;

  /** Clear all cached data and refetch from the beginning. */
  invalidate: () => void;
};

/**
 * Props for the generic VirtualList component.
 */
export type VirtualListProps<T> = {
  /** Data source from useOffsetVirtualData. */
  data: OffsetVirtualDataResult<T>;

  /** Render a loaded item. */
  renderItem: (item: T, index: number) => React.ReactNode;

  /** Render a placeholder for an item that hasn't loaded yet. */
  renderPlaceholder?: (index: number) => React.ReactNode;

  /** Stable key for each loaded item (used for React reconciliation). */
  getItemKey: (item: T, index: number) => string | number;

  /** Estimated height of one row in pixels (before measurement). */
  estimatedItemHeight: number;

  /** Extra rows rendered beyond the visible viewport (default: 5). */
  overscan?: number;

  /** Number of columns per row for grid layouts (default: 1). */
  columns?: number;

  /** Optional className for the outer scroll container. */
  className?: string;
};
