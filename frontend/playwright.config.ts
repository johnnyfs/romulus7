import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "../tests/acceptance/frontend",
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: `http://localhost:${process.env.FRONTEND_PORT ?? 5173}`,
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
  ],
});
