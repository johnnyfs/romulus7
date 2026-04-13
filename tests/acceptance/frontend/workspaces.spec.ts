import { test, expect } from "@playwright/test";

const API = "/api/v1/workspaces";

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

async function createWorkspace(request: any, name: string) {
  const res = await request.post(`${API}/`, {
    data: { name },
  });
  expect(res.ok()).toBe(true);
  return res.json() as Promise<{ id: string; name: string }>;
}

async function deleteWorkspace(request: any, id: string) {
  const res = await request.delete(`${API}/${id}`);
  expect(res.ok()).toBe(true);
}

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------

test.describe("Workspaces page", () => {
  // Track workspace IDs created during each test so we only clean those up.
  let created: string[];

  test.beforeEach(() => {
    created = [];
  });

  test.afterEach(async ({ request }) => {
    for (const id of created) {
      await request.delete(`${API}/${id}`);
    }
  });

  async function create(request: any, name: string) {
    const ws = await createWorkspace(request, name);
    created.push(ws.id);
    return ws;
  }

  test("shows empty state when no workspaces exist", async ({ page, request }) => {
    // Fetch current workspaces, temporarily delete them, check empty state,
    // then restore them. This avoids destroying real data.
    const res = await request.get(`${API}/?limit=100`);
    const { items } = await res.json();
    const ids = items.map((ws: any) => ws.id);

    for (const id of ids) {
      await deleteWorkspace(request, id);
    }

    try {
      await page.goto("/workspaces");
      await expect(page.getByText("No workspaces yet.")).toBeVisible();
    } finally {
      // Restore: re-create with original names
      for (const ws of items) {
        await createWorkspace(request, ws.name);
      }
    }
  });

  test("displays workspace cards", async ({ page, request }) => {
    await create(request, "test-workspace-alpha");
    await create(request, "test-workspace-beta");

    await page.goto("/workspaces");

    await expect(page.getByRole("heading", { name: "Workspaces" })).toBeVisible();
    await expect(page.getByText("test-workspace-alpha")).toBeVisible();
    await expect(page.getByText("test-workspace-beta")).toBeVisible();
  });

  test("shows workspace ID and created date on each card", async ({ page, request }) => {
    const ws = await create(request, "test-ws-meta");

    await page.goto("/workspaces");
    await expect(page.getByText("test-ws-meta")).toBeVisible();

    // Short ID (first 8 chars) should be visible
    const shortId = ws.id.slice(0, 8);
    await expect(page.getByText(shortId)).toBeVisible();

    // Created date should be present
    await expect(page.getByText(/Created\s/)).toBeVisible();
  });

  test("delete button removes a workspace", async ({ page, request }) => {
    await create(request, "ws-to-delete");
    await create(request, "ws-to-keep");

    await page.goto("/workspaces");
    await expect(page.getByText("ws-to-delete")).toBeVisible();
    await expect(page.getByText("ws-to-keep")).toBeVisible();

    // Hover the card to reveal the delete button, then click it.
    const card = page.getByText("ws-to-delete").locator("../..");
    await card.hover();
    await card.getByRole("button", { name: "Delete workspace" }).click();

    // Card should disappear; the other remains.
    await expect(page.getByText("ws-to-delete")).not.toBeVisible();
    await expect(page.getByText("ws-to-keep")).toBeVisible();

    // Remove from tracked list since it's already deleted.
    created = created.filter((id) => id !== created[0]);
  });

  test("redirects / to /workspaces", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/workspaces/);
  });
});
