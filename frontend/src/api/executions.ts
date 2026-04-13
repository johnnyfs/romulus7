/**
 * Execution API adapter.
 *
 * ABSTRACTION BOUNDARY: This is the ONLY file that knows the execution
 * endpoint URL and response shape.
 */
import type { FetchPageFn, PageResult } from "../components/virtual-list/types";

export type ExecutionSpec = {
  kind: string;
  commands: string[];
};

export type Execution = {
  id: string;
  created_at: string;
  updated_at: string;
  spec: ExecutionSpec;
};

/** Shape returned by GET /api/v1/executions/ */
type ExecutionListResponse = {
  items: Execution[];
  count: number;
};

/**
 * Fetch adapter for the execution list endpoint.
 * Q = void because we have no workspace filtering yet.
 */
export const fetchExecutionPage: FetchPageFn<Execution, void> = async ({
  offset,
  limit,
  signal,
}): Promise<PageResult<Execution>> => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const response = await fetch(`/api/v1/executions/?${params}`, { signal });
  if (!response.ok) {
    throw new Error(`Failed to fetch executions: ${response.status}`);
  }
  const data: ExecutionListResponse = await response.json();
  return { items: data.items };
};
