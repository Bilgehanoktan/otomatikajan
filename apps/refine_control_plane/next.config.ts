import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // output: 'export', // Comment out for local dev if routing is needed
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  /* eslint: {
    ignoreDuringBuilds: true,
  }, */
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1'}/:path*`,
      },
    ];
  },
};

export default nextConfig;