/**
 * Sandbox API adapter.
 *
 * ABSTRACTION BOUNDARY: This is the ONLY file that knows the sandbox
 * endpoint URL and response shape.
 */

export type Sandbox = {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  worker_lease_id: string | null;
};

type SandboxListResponse = {
  items: Sandbox[];
  count: number;
};

export async function fetchSandboxes(
  signal?: AbortSignal,
): Promise<Sandbox[]> {
  const params = new URLSearchParams({ limit: "100", offset: "0" });
  const response = await fetch(`/api/v1/sandboxes/?${params}`, { signal });
  if (!response.ok) {
    throw new Error(`Failed to fetch sandboxes: ${response.status}`);
  }
  const data: SandboxListResponse = await response.json();
  return data.items;
}
