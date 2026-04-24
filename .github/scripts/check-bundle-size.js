#!/usr/bin/env node
/**
 * check-bundle-size.js
 *
 * Checks that the first-load JS bundles for web-app and web-marketing
 * are within their defined budgets. Reads directly from the .next/static/chunks
 * directories — no npm dependencies required.
 *
 * Exits 0 if all budgets pass, 1 if any are exceeded.
 * Exits 0 with a warning if a .next directory is missing (build was skipped).
 *
 * Budgets (uncompressed):
 *   web-app      ≤ 300 KB  (auth-gated, slightly higher allowance)
 *   web-marketing ≤ 200 KB  (public surface, LCP critical)
 *
 * web-crisis is excluded — it is a static export with no chunk directory.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

// ─── Config ──────────────────────────────────────────────────────────────────

const REPO_ROOT = path.resolve(__dirname, '..', '..');

const SURFACES = [
  {
    name: 'web-app',
    dir: path.join(REPO_ROOT, 'apps', 'web-app'),
    budgetBytes: 300 * 1024,   // 300 KB uncompressed
    budgetLabel: '300 KB',
  },
  {
    name: 'web-marketing',
    dir: path.join(REPO_ROOT, 'apps', 'web-marketing'),
    budgetBytes: 200 * 1024,   // 200 KB uncompressed
    budgetLabel: '200 KB',
  },
];

const TOP_CHUNKS_TO_SHOW = 10;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatBytes(bytes) {
  if (bytes >= 1024 * 1024) {
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }
  return (bytes / 1024).toFixed(1) + ' KB';
}

/**
 * Recursively collect all .js files under a directory.
 */
function collectJsFiles(dir) {
  const results = [];
  if (!fs.existsSync(dir)) return results;

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectJsFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith('.js')) {
      results.push(fullPath);
    }
  }
  return results;
}

/**
 * Return gzip-compressed size of a file, or null if zlib fails.
 */
function gzipSize(filePath) {
  try {
    const buf = fs.readFileSync(filePath);
    return zlib.gzipSync(buf, { level: 9 }).length;
  } catch {
    return null;
  }
}

/**
 * Identify "framework + common" chunks that ship on every page (first-load JS).
 * Next.js places these in .next/static/chunks/ with names like:
 *   framework-<hash>.js
 *   main-<hash>.js
 *   webpack-<hash>.js
 *   <hash>.js  (shared chunks)
 *
 * Page-specific bundles live in .next/static/chunks/pages/ and are NOT counted
 * here — we measure the baseline payload every visitor downloads, not per-page.
 */
function isFirstLoadChunk(filePath) {
  const name = path.basename(filePath);
  const rel = filePath.replace(/\\/g, '/');

  // Exclude page-specific chunks
  if (rel.includes('/chunks/pages/')) return false;
  // Exclude app-router page segments
  if (rel.includes('/chunks/app/')) return false;

  // Include known first-load chunk prefixes
  return (
    name.startsWith('framework-') ||
    name.startsWith('main-') ||
    name.startsWith('webpack-') ||
    name.startsWith('polyfills-') ||
    // Shared chunks: numeric or short hash filenames at the chunks root level
    /^[0-9a-f]+-[0-9a-f]+\.js$/.test(name) ||
    /^[0-9a-f]{8,}\.js$/.test(name)
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

let anyFailed = false;

for (const surface of SURFACES) {
  const nextDir = path.join(surface.dir, '.next');
  const chunksDir = path.join(nextDir, 'static', 'chunks');

  console.log(`\n${'─'.repeat(60)}`);
  console.log(`Surface: ${surface.name}  (budget: ${surface.budgetLabel} uncompressed)`);
  console.log('─'.repeat(60));

  if (!fs.existsSync(nextDir)) {
    console.warn(`  [WARN] .next directory not found at ${nextDir}`);
    console.warn('         Build may have been skipped — treating as pass.');
    continue;
  }

  if (!fs.existsSync(chunksDir)) {
    console.warn(`  [WARN] chunks directory not found at ${chunksDir}`);
    console.warn('         Skipping budget check for this surface.');
    continue;
  }

  // Collect all JS files under .next/static/chunks (including subdirs for app router)
  const allChunks = collectJsFiles(chunksDir);

  if (allChunks.length === 0) {
    console.warn('  [WARN] No .js files found in chunks directory — skipping.');
    continue;
  }

  // Measure all chunks
  const measured = allChunks.map((filePath) => {
    const stat = fs.statSync(filePath);
    const gz = gzipSize(filePath);
    return {
      name: path.relative(path.join(surface.dir, '.next'), filePath).replace(/\\/g, '/'),
      rawBytes: stat.size,
      gzBytes: gz,
    };
  });

  // Sort by raw size descending for the table
  measured.sort((a, b) => b.rawBytes - a.rawBytes);

  // Print top-N table
  console.log(`\n  Top ${Math.min(TOP_CHUNKS_TO_SHOW, measured.length)} largest chunks:`);
  console.log(`  ${'Chunk'.padEnd(65)} ${'Raw'.padStart(10)}  ${'Gzip'.padStart(10)}`);
  console.log(`  ${'-'.repeat(65)} ${'-'.repeat(10)}  ${'-'.repeat(10)}`);

  for (const chunk of measured.slice(0, TOP_CHUNKS_TO_SHOW)) {
    const gzLabel = chunk.gzBytes != null ? formatBytes(chunk.gzBytes) : '     n/a';
    console.log(
      `  ${chunk.name.padEnd(65)} ${formatBytes(chunk.rawBytes).padStart(10)}  ${gzLabel.padStart(10)}`
    );
  }

  // Budget check: sum first-load chunks only
  const firstLoadChunks = measured.filter((c) =>
    isFirstLoadChunk(path.join(surface.dir, '.next', c.name))
  );

  const totalRaw = firstLoadChunks.reduce((sum, c) => sum + c.rawBytes, 0);
  const totalGz = firstLoadChunks.every((c) => c.gzBytes != null)
    ? firstLoadChunks.reduce((sum, c) => sum + (c.gzBytes ?? 0), 0)
    : null;

  const allChunksTotal = measured.reduce((sum, c) => sum + c.rawBytes, 0);

  console.log(`\n  First-load JS chunks matched: ${firstLoadChunks.length} of ${measured.length} total`);
  console.log(`  First-load total (raw):   ${formatBytes(totalRaw)}`);
  if (totalGz != null) {
    console.log(`  First-load total (gzip):  ${formatBytes(totalGz)}`);
  }
  console.log(`  All chunks total (raw):   ${formatBytes(allChunksTotal)}`);

  const exceeded = totalRaw > surface.budgetBytes;

  if (exceeded) {
    console.error(
      `\n  [FAIL] Budget exceeded: ${formatBytes(totalRaw)} > ${surface.budgetLabel}`
    );
    console.error(
      `         Reduce bundle size or raise the budget in .github/scripts/check-bundle-size.js`
    );
    anyFailed = true;
  } else {
    console.log(
      `\n  [PASS] Within budget: ${formatBytes(totalRaw)} ≤ ${surface.budgetLabel}`
    );
  }
}

console.log(`\n${'═'.repeat(60)}`);
if (anyFailed) {
  console.error('Bundle size check FAILED — at least one surface exceeded its budget.');
} else {
  console.log('Bundle size check PASSED — all surfaces within budget.');
}
console.log('═'.repeat(60));

process.exit(anyFailed ? 1 : 0);
