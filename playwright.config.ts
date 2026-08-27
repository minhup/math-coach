import { defineConfig, devices } from "@playwright/test";

const webPort = process.env.PLAYWRIGHT_WEB_PORT ?? "3000";
const apiPort = process.env.PLAYWRIGHT_API_PORT ?? "8000";
const webUrl = `http://localhost:${webPort}`;
const apiOrigin = `http://127.0.0.1:${apiPort}`;

export default defineConfig({
  expect: { timeout: 10_000 },
  fullyParallel: true,
  reporter: process.env.CI ? "github" : "list",
  retries: process.env.CI ? 2 : 0,
  testDir: "./tests/e2e",
  workers: 5,
  use: {
    baseURL: webUrl,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: process.env.PLAYWRIGHT_EXTERNAL_SERVERS
    ? undefined
    : [
        {
          command: `cd services/api && uv run uvicorn app.main:app --host 127.0.0.1 --port ${apiPort}`,
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
          url: `${apiOrigin}/api/v1/health`,
        },
        {
          command: "npm run dev:web",
          env: { API_PROXY_TARGET: apiOrigin, PORT: webPort },
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
          url: webUrl,
        },
      ],
  projects: [
    {
      name: "compact-chromium",
      use: {
        browserName: "chromium",
        hasTouch: true,
        viewport: { height: 640, width: 360 },
      },
    },
    { name: "pixel-7-chromium", use: { ...devices["Pixel 7"] } },
    { name: "iphone-13-webkit", use: { ...devices["iPhone 13"] } },
    { name: "ipad-pro-11-portrait-webkit", use: { ...devices["iPad Pro 11"] } },
    {
      name: "ipad-pro-11-landscape-webkit",
      use: {
        ...devices["iPad Pro 11"],
        screen: { height: 834, width: 1194 },
        viewport: { height: 834, width: 1194 },
      },
    },
  ],
});
