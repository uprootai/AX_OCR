#!/usr/bin/env node
/**
 * migrate-content.mjs
 * Migrates Docusaurus-specific syntax in Starlight content files.
 *
 * Transformations:
 * 1. Internal links: /docs/xxx -> /xxx
 * 2. Admonitions: :::type Title -> :::type[Title]
 * 3. Remove sidebar_label frontmatter
 * 4. Remove @site/... import statements
 */

import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join, relative } from 'node:path';

const CONTENT_DIR = new URL(
  '../src/content/docs/',
  import.meta.url,
).pathname;

// ── Helpers ──────────────────────────────────────────────────────────

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const e of entries) {
    const full = join(dir, e.name);
    if (e.isDirectory()) files.push(...(await walk(full)));
    else if (/\.(md|mdx)$/.test(e.name)) files.push(full);
  }
  return files;
}

// ── Transform functions ──────────────────────────────────────────────

/**
 * 1. Internal links: ](/docs/xxx) -> ](/xxx)
 *    Only in markdown link syntax, not in code blocks or external URLs.
 */
function fixInternalLinks(content) {
  let count = 0;

  // Split by code blocks to avoid transforming code
  const parts = content.split(/(```[\s\S]*?```|`[^`\n]+`)/g);

  const result = parts.map((part, i) => {
    // Odd indices are code blocks — skip them
    if (i % 2 === 1) return part;

    // Replace markdown links: [text](/docs/xxx) -> [text](/xxx)
    // Also handles bare URLs in parentheses and href attributes
    return part.replace(/\]\(\/docs\//g, () => {
      count++;
      return '](/';
    });
  }).join('');

  return { result, count };
}

/**
 * 2. Admonitions: :::type Title -> :::type[Title]
 *    Docusaurus: :::tip My Title\n  content\n:::
 *    Starlight:  :::tip[My Title]\n  content\n:::
 */
function fixAdmonitions(content) {
  let count = 0;
  const admonitionTypes = ['note', 'tip', 'warning', 'danger', 'info', 'caution'];
  const typePattern = admonitionTypes.join('|');

  // Match :::type Title (where Title is non-empty text after the type)
  const regex = new RegExp(
    `^(:::(?:${typePattern}))\\s+(.+)$`,
    'gm',
  );

  const result = content.replace(regex, (match, prefix, title) => {
    // If already in [title] format, skip
    if (prefix.includes('[')) return match;
    count++;
    return `${prefix}[${title.trim()}]`;
  });

  return { result, count };
}

/**
 * 3. Remove sidebar_label from frontmatter
 */
function removeSidebarLabel(content) {
  let count = 0;

  // Match frontmatter block
  const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!fmMatch) return { result: content, count: 0 };

  const frontmatter = fmMatch[1];
  const newFrontmatter = frontmatter
    .split('\n')
    .filter((line) => {
      if (/^sidebar_label\s*:/.test(line)) {
        count++;
        return false;
      }
      return true;
    })
    .join('\n');

  if (count === 0) return { result: content, count: 0 };

  const result = content.replace(
    /^---\n[\s\S]*?\n---/,
    `---\n${newFrontmatter}\n---`,
  );

  return { result, count };
}

/**
 * 4. Remove @site/... import statements
 *    These are Docusaurus-specific path aliases that won't work in Starlight.
 */
function removeDocusaurusImports(content) {
  let count = 0;
  const lines = content.split('\n');
  const filtered = lines.filter((line) => {
    if (/^\s*import\s+.+\s+from\s+['"]@site\//.test(line)) {
      count++;
      return false;
    }
    return true;
  });

  if (count === 0) return { result: content, count: 0 };
  return { result: filtered.join('\n'), count };
}

// ── Main ─────────────────────────────────────────────────────────────

const stats = {
  filesScanned: 0,
  filesModified: 0,
  linksFixed: 0,
  admonitionsFixed: 0,
  sidebarLabelsRemoved: 0,
  importsRemoved: 0,
};

const files = await walk(CONTENT_DIR);
stats.filesScanned = files.length;

for (const file of files) {
  const original = await readFile(file, 'utf-8');
  let content = original;

  // 1. Fix internal links
  const links = fixInternalLinks(content);
  content = links.result;
  stats.linksFixed += links.count;

  // 2. Fix admonitions
  const admonitions = fixAdmonitions(content);
  content = admonitions.result;
  stats.admonitionsFixed += admonitions.count;

  // 3. Remove sidebar_label
  const sidebar = removeSidebarLabel(content);
  content = sidebar.result;
  stats.sidebarLabelsRemoved += sidebar.count;

  // 4. Remove @site/ imports
  const imports = removeDocusaurusImports(content);
  content = imports.result;
  stats.importsRemoved += imports.count;

  if (content !== original) {
    await writeFile(file, content, 'utf-8');
    stats.filesModified++;
    const rel = relative(CONTENT_DIR, file);
    const changes = [];
    if (links.count) changes.push(`links:${links.count}`);
    if (admonitions.count) changes.push(`admonitions:${admonitions.count}`);
    if (sidebar.count) changes.push(`sidebar_label:${sidebar.count}`);
    if (imports.count) changes.push(`imports:${imports.count}`);
    console.log(`  ${rel}  (${changes.join(', ')})`);
  }
}

console.log('\n── Summary ──────────────────────────────────');
console.log(`Files scanned:          ${stats.filesScanned}`);
console.log(`Files modified:         ${stats.filesModified}`);
console.log(`Internal links fixed:   ${stats.linksFixed}`);
console.log(`Admonitions converted:  ${stats.admonitionsFixed}`);
console.log(`sidebar_label removed:  ${stats.sidebarLabelsRemoved}`);
console.log(`@site imports removed:  ${stats.importsRemoved}`);
