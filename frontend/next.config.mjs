/**
 * Next.js Configuration
 * Optimized for performance, SEO, and production deployment
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode
  reactStrictMode: true,

  // Experimental features
  experimental: {
    // Enable the latest React features
    ppr: false, // Partial Prerendering (when stable)

    // Optimize CSS
    optimizeCss: true,

    // Enable server components logging
    logging: {
      level: 'info',
      fullUrl: true,
    },
  },

  // Internationalization
  i18n: {
    locales: ['en', 'ja', 'es', 'fr', 'de'],
    defaultLocale: 'en',
    localeDetection: true,
    domains: [
      {
        domain: 'jobmatch.pro',
        defaultLocale: 'en',
      },
      {
        domain: 'jp.jobmatch.pro',
        defaultLocale: 'ja',
      },
      {
        domain: 'es.jobmatch.pro',
        defaultLocale: 'es',
      },
      {
        domain: 'fr.jobmatch.pro',
        defaultLocale: 'fr',
      },
      {
        domain: 'de.jobmatch.pro',
        defaultLocale: 'de',
      },
    ],
  },

  // Image optimization
  images: {
    domains: [
      'localhost',
      'jobmatch.pro',
      'api.jobmatch.pro',
      'cdn.jobmatch.pro',
      's3.amazonaws.com',
      'images.unsplash.com',
      'avatars.githubusercontent.com',
      'lh3.googleusercontent.com',
    ],
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60,
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },

  // Performance optimizations
  compiler: {
    // Remove console logs in production
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },

  // Bundle analyzer (enable with ANALYZE=true)
  ...(process.env.ANALYZE === 'true' && {
    webpack: (config, { isServer }) => {
      if (!isServer) {
        const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
        config.plugins.push(
          new BundleAnalyzerPlugin({
            analyzerMode: 'static',
            openAnalyzer: false,
            reportFilename: '../bundle-analyzer.html',
          })
        );
      }
      return config;
    },
  }),

  // Headers for security and performance
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          // Security headers
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
          // Performance headers
          {
            key: 'X-Powered-By',
            value: '',
          },
        ],
      },
      {
        source: '/api/(.*)',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: process.env.ALLOWED_ORIGINS || '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
        ],
      },
      {
        source: '/sitemap.xml',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=86400, stale-while-revalidate=86400',
          },
        ],
      },
      {
        source: '/(.*\\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2))',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },

  // Redirects
  async redirects() {
    return [
      // Redirect old job URLs
      {
        source: '/job/:id',
        destination: '/jobs/:id',
        permanent: true,
      },
      // Redirect old company URLs
      {
        source: '/company/:id',
        destination: '/companies/:id',
        permanent: true,
      },
      // Redirect old user URLs
      {
        source: '/user/:path*',
        destination: '/profile/:path*',
        permanent: true,
      },
    ];
  },

  // Rewrites for API proxy
  async rewrites() {
    return [
      {
        source: '/sitemap.xml',
        destination: '/api/sitemap',
      },
      {
        source: '/robots.txt',
        destination: '/api/robots',
      },
    ];
  },

  // Environment variables
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // Output configuration
  output: 'standalone',

  // TypeScript configuration
  typescript: {
    ignoreBuildErrors: false,
  },

  // ESLint configuration
  eslint: {
    ignoreDuringBuilds: false,
    dirs: ['app', 'components', 'lib', 'types'],
  },

  // Webpack configuration
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Analyze bundle in development
    if (dev && !isServer) {
      config.devtool = 'cheap-module-source-map';
    }

    // Add bundle analyzer
    if (process.env.ANALYZE === 'true' && !isServer) {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          openAnalyzer: false,
          reportFilename: '../bundle-analyzer.html',
        })
      );
    }

    // Optimize chunks
    config.optimization = {
      ...config.optimization,
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          },
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
          },
        },
      },
    };

    return config;
  },

  // Runtime configuration
  publicRuntimeConfig: {
    NODE_ENV: process.env.NODE_ENV,
  },

  // Server runtime configuration
  serverRuntimeConfig: {
    // Server-only secrets go here
  },

  // Trailing slash
  trailingSlash: false,

  // Power by header
  poweredByHeader: false,

  // Compression
  compress: true,

  // Generate etags
  generateEtags: true,

  // Disable x-powered-by header
  poweredByHeader: false,
};

export default nextConfig;