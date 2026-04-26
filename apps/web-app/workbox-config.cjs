const { generateSW } = require('workbox-build');

generateSW({
  globDirectory: '../web-crisis/out/',
  globPatterns: [
    'en/crisis/**/*.html',
  ],
  swDest: 'public/sw.js',
  runtimeCaching: [],
  skipWaiting: true,
  clientsClaim: true,
}).then(({ count, size }) => {
  console.log(`Generated SW: precached ${count} files, ${size} bytes`);
}).catch(console.error);
