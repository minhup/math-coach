import type { NextConfig } from "next";

const apiPort = process.env.PLAYWRIGHT_API_PORT ?? "8000";
const apiTarget = process.env.API_PROXY_TARGET ?? `http://127.0.0.1:${apiPort}`;

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiTarget}/api/:path*` }];
  },
  transpilePackages: ["@math-coach/api-client"],
};

export default nextConfig;
