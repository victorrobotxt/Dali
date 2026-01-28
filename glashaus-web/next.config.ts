import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 1. Enable Standalone Output for Docker
  output: "standalone",
  
  reactCompiler: true,
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.focus.bg',
      },
      {
        protocol: 'https',
        hostname: 'imot.bg',
      }
    ],
  },
};

export default nextConfig;