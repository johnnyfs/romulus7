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
