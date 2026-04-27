const path = require('path');
const { generateSW } = require('workbox-build');

// Offline contract: precaches only the static HTML shells for the 3 day-one locales.
// JS chunks (_next/static/**) are NOT precached by design — the crisis surface degrades
// gracefully to static HTML + tel:/sms: links with JS disabled (CLAUDE.md Rule 1).
generateSW({
  globDirectory: path.resolve(__dirname, '../web-crisis/out/'),
  globPatterns: [
    'en/index.html',
    'ar/index.html',
    'fa/index.html',
  ],
  swDest: path.resolve(__dirname, 'public/sw.js'),
  runtimeCaching: [],
  skipWaiting: true,
  clientsClaim: true,
}).then(({ count, size }) => {
  console.log(`Generated SW: precached ${count} files, ${size} bytes`);
}).catch(console.error);
