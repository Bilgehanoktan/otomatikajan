import type { NextConfig } from 'next';
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin();

const isDev = process.env.NODE_ENV !== 'production';
const backendOrigin = (
  (isDev
    ? (process.env.BACKEND_ORIGIN || process.env.NEXT_PUBLIC_BACKEND_ORIGIN)
    : (process.env.BACKEND_ORIGIN || process.env.NEXT_PUBLIC_BACKEND_ORIGIN || process.env.NEXT_PUBLIC_API_URL)) ||
  'http://127.0.0.1:8000'
).replace(/\/api\/v1\/?$/, '');

const nextConfig: NextConfig = {
  // output: 'export', // Comment out for local dev if routing is needed
  trailingSlash: false,
  allowedDevOrigins: ["127.0.0.1", "localhost"],
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
        source: '/api/v1/:path*/',
        destination: `${backendOrigin}/api/v1/:path*`,
      },
      {
        source: '/api/v1/:path*',
        destination: `${backendOrigin}/api/v1/:path*`,
      },
      {
        source: '/docs',
        destination: `${backendOrigin}/docs`,
      },
      {
        source: '/redoc',
        destination: `${backendOrigin}/redoc`,
      },
      {
        source: '/openapi.json',
        destination: `${backendOrigin}/openapi.json`,
      },
      {
        source: '/api/mcp/:path*',
        destination: `${backendOrigin}/api/mcp/:path*`,
      },
      {
        source: '/api/agents',
        destination: `${backendOrigin}/api/v1/harness/agents`,
      },
      {
        source: '/api/agents/:path*',
        destination: `${backendOrigin}/api/v1/harness/agents/:path*`,
      },
      {
        source: '/api/models/:path*',
        destination: `${backendOrigin}/api/models/:path*`,
      },
      {
        source: '/ws/:path*',
        destination: `${backendOrigin}/ws/:path*`,
      },
    ];
  },
};

export default withNextIntl(nextConfig);
