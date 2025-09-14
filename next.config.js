/** @type {import('next').NextConfig} */
const nextConfig = {
  // React strict mode for better development experience
  reactStrictMode: true,

  // Enable SWC minifier for better performance
  swcMinify: true,

  // Experimental features
  experimental: {
    // Enable app directory (App Router)
    appDir: true,
    // Server components experimental features
    serverComponentsExternalPackages: [],
  },

  // Image optimization configuration
  images: {
    domains: [],
    formats: ['image/webp', 'image/avif'],
  },

  // Environment variables to expose to the browser
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // Redirect configuration
  async redirects() {
    return [
      // Redirect examples
      // {
      //   source: '/old-page',
      //   destination: '/new-page',
      //   permanent: true,
      // },
    ];
  },

  // Rewrite configuration
  async rewrites() {
    return [
      // Rewrite examples
      // {
      //   source: '/api/:path*',
      //   destination: 'https://api.example.com/:path*',
      // },
    ];
  },

  // Headers configuration
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },

  // Webpack configuration
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Custom webpack configurations
    
    // Ignore certain packages in server-side builds
    if (isServer) {
      config.externals.push({
        'utf-8-validate': 'commonjs utf-8-validate',
        'bufferutil': 'commonjs bufferutil',
      });
    }

    return config;
  },

  // TypeScript configuration
  typescript: {
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    ignoreBuildErrors: false,
  },

  // ESLint configuration
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: false,
  },

  // Compiler options
  compiler: {
    // Remove console logs in production
    removeConsole: process.env.NODE_ENV === 'production',
    // Enable styled-components support
    styledComponents: true,
  },

  // Output configuration
  output: 'standalone', // For Docker deployment
  
  // Trailing slash configuration
  trailingSlash: false,

  // PoweredBy header configuration
  poweredByHeader: false,

  // Compression configuration
  compress: true,

  // Development configuration
  devIndicators: {
    buildActivity: true,
  },
};

module.exports = nextConfig;