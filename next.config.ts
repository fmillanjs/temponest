import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  serverExternalPackages: ['@prisma/client'],
  transpilePackages: ['@trpc/server', '@trpc/client', '@trpc/next', '@trpc/react-query'],
};

export default nextConfig;
