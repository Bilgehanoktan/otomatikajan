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
  trailingSlash: true,
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
        source: '/api/v1/:path*',
        destination: `${backendOrigin}/api/v1/:path*`,
      },
      {
        source: '/ws/:path*',
        destination: `${backendOrigin}/ws/:path*`,
      },
    ];
  },
};

export default withNextIntl(nextConfig);
