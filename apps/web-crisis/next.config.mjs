/** @type {import('next').NextConfig} */
const nextConfig = {
  // Full static export. The build output in `out/` is self-contained HTML+CSS+minimal JS.
  // Deploy target: S3 + CloudFront (or any CDN) behind a 99.99% SLO.
  output: 'export',
  reactStrictMode: true,
  poweredByHeader: false,
  images: {
    unoptimized: true,
  },
  transpilePackages: ['@disciplineos/design-system', '@disciplineos/safety-directory'],
  trailingSlash: true,
};

export default nextConfig;
