/** @type {import('next').NextConfig} */

const nextConfig = {
  basePath: "/webui",
  reactStrictMode: false,
  allowedDevOrigins: ['192.168.0.*', 'localhost'],
  // Configure for development
  ...(process.env.NODE_ENV === 'development' && {
    assetPrefix: "/webui",
  }),
}

// Only apply static export settings for production builds
if (process.env.NODE_ENV === 'production') {
  nextConfig.output = 'export';
  nextConfig.distDir = 'out';
  nextConfig.trailingSlash = true;
  nextConfig.images = { unoptimized: true };
}

module.exports = nextConfig
