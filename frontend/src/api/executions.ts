/**
 * Execution API adapter.
 *
 * ABSTRACTION BOUNDARY: This is the ONLY file that knows the execution
 * endpoint URL and response shape.
 */
import type { FetchPageFn, PageResult } from "../components/virtual-list/types";

export type ExecutionSpec = {
  kind: string;
  command: string;
};

export type Execution = {
  id: string;
  created_at: string;
  updated_at: string;
  name: string;
  spec: ExecutionSpec;
  dispatch_id: string | null;
};

type DispatchResponse = {
  id: string;
  execution_id: string;
  worker_response: unknown;
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

export async function createExecution(
  payload: { name: string; spec: ExecutionSpec },
): Promise<Execution> {
  const response = await fetch("/api/v1/executions/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Failed to create execution: ${response.status}`);
  }
  return response.json();
}

export async function dispatchExecution(
  executionId: string,
  params: { sandbox_id?: string | null },
): Promise<DispatchResponse> {
  const response = await fetch(`/api/v1/executions/${executionId}/dispatch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sandbox_id: params.sandbox_id ?? null,
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to dispatch execution: ${response.status}`);
  }
  return response.json();
}

export async function deleteExecution(
  executionId: string,
): Promise<{ id: string; deleted: boolean }> {
  const response = await fetch(`/api/v1/executions/${executionId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete execution: ${response.status}`);
  }
  return response.json();
}
