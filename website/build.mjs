import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import MarkdownIt from 'markdown-it';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.dirname(here);
const manual = path.join(repo, 'manual');
export const base = process.env.SITE_BASE || '/';
if (!/^\/(?:[a-zA-Z0-9_-]+\/)*$/.test(base)) throw new Error('SITE_BASE must be a slash-delimited URL path.');
const origin = process.env.SITE_URL ? new URL(process.env.SITE_URL) : null;
if (origin && (!['https:', 'http:'].includes(origin.protocol) || origin.pathname !== '/' || origin.search || origin.hash || origin.username || origin.password)) {
  throw new Error('SITE_URL must be an HTTP(S) origin without a path or credentials.');
}
const sourceRoot = 'https://github.com/meerzulee/omarchy-psx';
const kernelRoot = 'https://github.com/meerzulee/linux-psx';
const downloads = 'https://t.me/omarchy_psx';
const escape = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const slug = value => value.toLowerCase().replace(/[^\p{L}\p{N}\s_-]/gu, '').trim().replace(/\s/g, '-');
const manifest = [
  ['01-welcome-to-omarchy-psx.md', '', 'Welcome to Omarchy psX!'],
  ['02-getting-started.md', 'getting-started', 'Getting Started'],
  ['03-first-boot.md', 'first-boot', 'First Boot'],
  ['04-the-desktop.md', 'the-desktop', 'The Desktop'],
  ['05-whats-different-on-ps4.md', 'whats-different-on-ps4', "What's Different on PS4"],
  ['06-networking.md', 'networking', 'Networking'],
  ['07-storage.md', 'storage', 'Storage'],
  ['08-kernels-and-firmware.md', 'kernels-and-firmware', 'Kernels and Firmware'],
  ['09-what-works.md', 'what-works', 'What Works'],
  ['10-recovery.md', 'recovery', 'Recovery'],
  ['11-troubleshooting.md', 'troubleshooting', 'Troubleshooting'],
  ['12-faq.md', 'faq', 'FAQ'],
  ['13-building-from-source.md', 'building-from-source', 'Building from Source'],
  ['14-contributing.md', 'contributing', 'Contributing'],
  ['15-legal-notice.md', 'legal-notice', 'Legal Notice'],
  ['README.md', 'toc', 'Table of Contents'],
];
const filenames = (await fs.readdir(manual)).filter(name => /^\d+.*\.md$/.test(name)).sort();
if (filenames.join() !== manifest.slice(0, 15).map(item => item[0]).join()) {
  throw new Error('The chapter allowlist must match the numbered manual chapters.');
}
const md = new MarkdownIt({ html: false, linkify: false, typographer: false });
const pages = await Promise.all(manifest.map(async ([file, route, title]) => {
  const source = path.join(manual, file);
  const text = (await fs.readFile(source, 'utf8')).split('\n<!-- manual-navigation -->')[0];
  const tokens = md.parse(text, {});
  const headings = new Set();
  const counts = new Map();
  for (let i = 0; i < tokens.length; i++) {
    if (tokens[i].type !== 'heading_open') continue;
    const name = slug(tokens[i + 1].content);
    const occurrence = counts.get(name) || 0;
    counts.set(name, occurrence + 1);
    const id = occurrence ? `${name}-${occurrence}` : name;
    tokens[i].attrSet('id', id);
    headings.add(id);
  }
  if (tokens.filter(token => token.type === 'heading_open' && token.tag === 'h1').length !== 1) {
    throw new Error(`${file} must have exactly one top-level heading.`);
  }
  const paragraphs = tokens.filter(token => token.type === 'inline').map(token => token.children?.map(child => child.content).join('') || token.content);
  const sections = tokens.flatMap((token, i) => token.type === 'heading_open' ? [tokens[i + 1].content] : []);
  return { file, source, route, title, text, tokens, headings, sections, body: paragraphs.join(' '), description: paragraphs[1]?.slice(0, 220) || title, url: base + (route ? route + '/' : '') };
}));
const bySource = new Map(pages.map(page => [page.source, page]));
const links = new Set();
const images = new Set();
let localLinks = 0;
async function rewrite(url, page, image = false) {
  if (/^(?:https?:|mailto:)/i.test(url)) return url;
  if (/^(?:[a-z]+:|\/\/|\/)/i.test(url)) throw new Error(`Unsupported link in ${page.file}: ${url}`);
  const [name, hash = ''] = url.split('#');
  const target = name ? path.resolve(path.dirname(page.source), decodeURIComponent(name)) : page.source;
  if (!target.startsWith(repo + path.sep)) throw new Error(`Link escapes the repository: ${url}`);
  const fragment = hash ? '#' + hash : '';
  const article = bySource.get(target);
  if (article) {
    if (hash && !article.headings.has(decodeURIComponent(hash))) throw new Error(`Missing heading in ${page.file}: ${url}`);
    localLinks++;
    return article.url + fragment;
  }
  const stat = await fs.stat(target).catch(() => null);
  if (!stat) throw new Error(`Missing target in ${page.file}: ${url}`);
  if (image) {
    if (!target.startsWith(path.join(manual, 'images') + path.sep) || !/\.(?:webp|png|jpe?g|svg)$/i.test(target)) {
      throw new Error(`Image must belong to manual/images: ${url}`);
    }
    images.add(target);
    return base + 'assets/images/' + path.basename(target);
  }
  const relative = path.relative(repo, target).split(path.sep).map(encodeURIComponent).join('/');
  links.add(relative);
  return `${sourceRoot}/${stat.isDirectory() ? 'tree' : 'blob'}/master/${relative}${fragment}`;
}
async function visit(tokens, page) {
  for (const token of tokens) {
    if (token.type === 'link_open') token.attrSet('href', await rewrite(token.attrGet('href'), page));
    if (token.type === 'image') {
      token.attrSet('src', await rewrite(token.attrGet('src'), page, true));
      token.attrSet('loading', 'lazy');
      token.attrSet('decoding', 'async');
    }
    if (token.children) await visit(token.children, page);
  }
}
for (const page of pages) await visit(page.tokens, page);
md.renderer.rules.table_open = () => '<div class="table-scroll" tabindex="0" role="region" aria-label="Reference table"><table>\n';
md.renderer.rules.table_close = () => '</table></div>\n';

// Canonical upstream Omarchy outlines and PSX in its Delta Corps Priest 1
// lettering. The static SVG needs no font download; see BRANDING.md for pins.
const wordmarkSvg = (await fs.readFile(path.join(here, 'assets/omarchy-psx.svg'), 'utf8')).trim();
const wordmark = `<div class="wordmark">${wordmarkSvg}</div><p class="manual-label">THE PLAYSTATION MANUAL</p>`;
function template(page, index) {
  const chapters = pages.slice(0, 15);
  const toc = pages[15];
  const previous = index > 0 && index < 15 ? chapters[index - 1] : null;
  const next = index < 14 ? chapters[index + 1] : null;
  const navigation = chapters.map((item, n) => `<li><a href="${item.url}"${item === page ? ' aria-current="page"' : ''}><span class="chapter-number">${String(n + 1).padStart(2, '0')}</span>${escape(item.title.replace(/!$/, ''))}</a></li>`).join('\n');
  const canonical = origin ? `<link rel="canonical" href="${escape(new URL(page.url, origin).href)}">` : '';
  return `<!doctype html>
<html lang="en" data-site-base="${base}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escape(page.title)} — Omarchy psX</title>
<meta name="description" content="${escape(page.description)}">
<meta name="theme-color" content="#1a1b26">
${canonical}
<link rel="icon" href="${base}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="${base}assets/manual.css">
<script src="${base}assets/manual.js" defer></script>
</head>
<body>
<a class="skip-link" href="#content">Skip to content</a>
<header class="site-header"><a class="site-name" href="${base}" aria-label="Omarchy psX manual home">${wordmarkSvg}</a><nav aria-label="Project links"><a class="manual-link" href="${toc.url}">The manual</a><a href="${downloads}" aria-label="Downloads on Telegram">Downloads</a><a href="${kernelRoot}">Linux psX <span aria-hidden="true">↗</span></a><a class="source-link" href="${sourceRoot}">GitHub <span aria-hidden="true">↗</span></a><button class="theme-toggle" type="button" hidden aria-label="Switch to light theme">◐</button></nav></header>
<div class="manual-layout">
<aside class="sidebar" aria-label="Manual navigation">
<button class="search-open" type="button" hidden><span>Search the manual</span><kbd>/</kbd></button>
<details class="chapter-panel" open><summary>Chapters <span>15</span></summary><nav aria-label="Chapters"><ol>${navigation}</ol><a class="contents-link" href="${toc.url}"${page === toc ? ' aria-current="page"' : ''}>Table of Contents</a></nav></details>
<p class="sidebar-note">Omarchy on PlayStation.<br>Powered by <a href="${kernelRoot}">Linux psX</a>.</p>
</aside>
<main id="content" tabindex="-1">
<div class="masthead">${wordmark}</div>
<article>${md.renderer.render(page.tokens, md.options, {})}</article>
<nav class="pagination" aria-label="Chapter pagination">${previous ? `<a href="${previous.url}" rel="prev"><span>Previous</span>← ${escape(previous.title)}</a>` : '<span></span>'}<a class="pagination-contents" href="${toc.url}">Contents</a>${next ? `<a class="pagination-next" href="${next.url}" rel="next"><span>Next</span>${escape(next.title)} →</a>` : '<span></span>'}</nav>
<footer class="page-footer"><p>An independent community port. <a href="${pages[14].url}">Licenses &amp; credits</a>.</p><p><a href="${downloads}">Downloads on Telegram ↗</a> · <a href="${sourceRoot}">Source on GitHub ↗</a></p></footer>
</main>
</div>
<dialog class="search-dialog" aria-labelledby="search-title"><form method="dialog"><div class="search-heading"><h2 id="search-title">Search the manual</h2><button aria-label="Close search">Esc</button></div></form><label class="sr-only" for="manual-search">Search words</label><input type="search" id="manual-search" placeholder="Try networking, recovery, firmware…" autocomplete="off" spellcheck="false"><p id="search-status" role="status">Search all fifteen chapters.</p><ul id="search-results" aria-label="Search results"></ul></dialog>
</body></html>\n`;
}
const html = pages.map(template);
const report = `${pages.length} pages, ${localLinks} internal links/anchors, ${images.size} manual images; ${links.size} source references remain external.`;
if (process.argv.includes('--check')) {
  console.log(`PASS: ${report}`);
} else {
  const output = path.join(here, 'dist');
  const temporary = path.join(here, 'dist-next');
  await fs.rm(temporary, { recursive: true, force: true });
  await fs.mkdir(path.join(temporary, 'assets/images'), { recursive: true });
  for (let i = 0; i < pages.length; i++) {
    const folder = path.join(temporary, pages[i].route);
    await fs.mkdir(folder, { recursive: true });
    await fs.writeFile(path.join(folder, 'index.html'), html[i]);
  }
  for (const name of ['manual.css', 'manual.js', 'favicon.svg', 'omarchy-psx.svg', 'psx.svg', 'psx.txt', 'omarchy-psx-square-tokyo-night.svg', 'LICENSE-omarchy.txt']) await fs.copyFile(path.join(here, 'assets', name), path.join(temporary, 'assets', name));
  await fs.copyFile(path.join(here, '_headers'), path.join(temporary, '_headers'));
  await fs.copyFile(path.join(repo, 'LICENSE'), path.join(temporary, 'LICENSE.txt'));
  for (const image of images) await fs.copyFile(image, path.join(temporary, 'assets/images', path.basename(image)));
  await fs.writeFile(path.join(temporary, 'search-index.json'), JSON.stringify(pages.map(({ title, url, body, sections }) => ({ title, url, body, sections }))) + '\n');
  await fs.writeFile(path.join(temporary, '.nojekyll'), '');
  if (origin) {
    await fs.writeFile(path.join(temporary, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${pages.map(page => `<url><loc>${escape(new URL(page.url, origin).href)}</loc></url>`).join('')}</urlset>\n`);
    await fs.writeFile(path.join(temporary, 'robots.txt'), `User-agent: *\nAllow: /\nSitemap: ${new URL(base + 'sitemap.xml', origin).href}\n`);
  }
  await fs.rm(output, { recursive: true, force: true });
  await fs.rename(temporary, output);
  console.log(`Built ${report}\nOutput: ${output}`);
}
