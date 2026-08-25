import { defineConfig, devices } from "@playwright/test";

const webUrl = "http://localhost:3000";
const apiUrl = "http://127.0.0.1:8000/api/v1/health";

export default defineConfig({
  expect: { timeout: 10_000 },
  fullyParallel: true,
  reporter: process.env.CI ? "github" : "list",
  retries: process.env.CI ? 2 : 0,
  testDir: "./tests/e2e",
  use: {
    baseURL: webUrl,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: process.env.PLAYWRIGHT_EXTERNAL_SERVERS
    ? undefined
    : [
        {
          command: "cd services/api && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000",
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
          url: apiUrl,
        },
        {
          command: "npm run dev:web",
          env: { API_PROXY_TARGET: "http://127.0.0.1:8000" },
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
