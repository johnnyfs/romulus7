/**
 * Workspace API adapter.
 *
 * ABSTRACTION BOUNDARY: This is the ONLY file that knows the workspace
 * endpoint URL and response shape. The reusable virtual-list layer
 * receives a generic `FetchPageFn` and never sees URLs or backend schemas.
 */
import type { FetchPageFn, PageResult } from "../components/virtual-list/types";

export type Workspace = {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
};

/** Shape returned by GET /api/v1/workspaces/ */
type WorkspaceListResponse = {
  items: Workspace[];
  count: number;
};

/**
 * Fetch adapter for the workspace list endpoint.
 * Q = void because the workspace list has no search/filter parameters (yet).
 */
export const fetchWorkspacePage: FetchPageFn<Workspace, void> = async ({
  offset,
  limit,
  signal,
}): Promise<PageResult<Workspace>> => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const response = await fetch(`/api/v1/workspaces/?${params}`, { signal });
  if (!response.ok) {
    throw new Error(`Failed to fetch workspaces: ${response.status}`);
  }
  const data: WorkspaceListResponse = await response.json();
  return { items: data.items };
};

export async function createWorkspace(
  name: string,
): Promise<Workspace> {
  const response = await fetch("/api/v1/workspaces/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create workspace: ${response.status}`);
  }
  return response.json();
}

export async function deleteWorkspace(
  workspaceId: string,
  signal?: AbortSignal,
): Promise<{ id: string; deleted: boolean }> {
  const response = await fetch(`/api/v1/workspaces/${workspaceId}`, {
    method: "DELETE",
    signal,
  });
  if (!response.ok) {
    throw new Error(`Failed to delete workspace: ${response.status}`);
  }
  return response.json();
}
