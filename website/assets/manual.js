const root = document.documentElement;
const themeButton = document.querySelector('.theme-toggle');
try { if (localStorage.getItem('omarchy-psx-theme') === 'light') root.dataset.theme = 'light'; } catch {}
function themeLabel() { themeButton.setAttribute('aria-label', `Switch to ${root.dataset.theme === 'light' ? 'dark' : 'light'} theme`); }
themeButton.hidden = false;
themeLabel();
themeButton.addEventListener('click', () => {
  root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
  try { localStorage.setItem('omarchy-psx-theme', root.dataset.theme); } catch {}
  themeLabel();
});

const panel = document.querySelector('.chapter-panel');
const small = matchMedia('(max-width: 800px)');
panel.open = !small.matches;
small.addEventListener('change', () => { panel.open = !small.matches; });

const trigger = document.querySelector('.search-open');
const dialog = document.querySelector('.search-dialog');
const input = document.querySelector('#manual-search');
const results = document.querySelector('#search-results');
const status = document.querySelector('#search-status');
let indexPromise;
async function search() {
  results.replaceChildren();
  const query = input.value.trim().toLowerCase();
  if (!query) { status.textContent = 'Search all fifteen chapters.'; return; }
  status.textContent = 'Searching…';
  try {
    indexPromise ||= fetch(`${root.dataset.siteBase}search-index.json`).then(response => {
      if (!response.ok) throw new Error('Search index unavailable');
      return response.json();
    }).catch(error => { indexPromise = null; throw error; });
    const index = await indexPromise;
    if (input.value.trim().toLowerCase() !== query) return;
    const words = query.split(/\s+/).filter(Boolean);
    const matches = index.map(page => {
      const title = page.title.toLowerCase();
      const body = page.body.toLowerCase();
      if (!words.every(word => title.includes(word) || body.includes(word))) return null;
      const headings = (page.sections || []).map(section => section.toLowerCase());
      const score = words.reduce((total, word) => total + (title.includes(word) ? 10 : 1) + (headings.some(heading => heading.includes(word)) ? 5 : 0), 0) + (headings.includes(query) ? 15 : 0);
      return { ...page, score };
    }).filter(Boolean).sort((a, b) => b.score - a.score);
    for (const page of matches) {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = page.url;
      const title = document.createElement('strong');
      title.textContent = page.title;
      const excerpt = document.createElement('span');
      const start = Math.max(0, page.body.toLowerCase().indexOf(words[0]) - 60);
      excerpt.textContent = (start ? '…' : '') + page.body.slice(start, start + 190) + (page.body.length > start + 190 ? '…' : '');
      link.append(title, excerpt);
      item.append(link);
      results.append(item);
    }
    status.textContent = matches.length ? `${matches.length} result${matches.length === 1 ? '' : 's'}. Use Tab or ↓ to choose a chapter.` : 'No matching chapters. Try a shorter search.';
  } catch { status.textContent = 'Search could not load. Use the chapter list, or try again.'; }
}
function openSearch() {
  if (dialog.open) return;
  dialog.showModal();
  input.focus();
  search();
}
trigger.hidden = false;
trigger.addEventListener('click', openSearch);
input.addEventListener('input', search);
input.addEventListener('keydown', event => {
  const first = results.querySelector('a');
  if (event.key === 'ArrowDown' && first) { event.preventDefault(); first.focus(); }
  if (event.key === 'Enter' && first) { event.preventDefault(); first.click(); }
});
dialog.addEventListener('close', () => trigger.focus());
document.addEventListener('keydown', event => {
  const editing = event.target.closest?.('input, textarea, select, [contenteditable="true"]');
  if ((event.key === '/' && !editing && !event.metaKey && !event.ctrlKey) || (event.key.toLowerCase() === 'k' && (event.metaKey || event.ctrlKey))) {
    event.preventDefault();
    openSearch();
  }
});
if (navigator.clipboard) {
  document.querySelectorAll('article pre').forEach(pre => {
    const code = pre.querySelector('code');
    if (!code) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy-code';
    button.textContent = 'Copy';
    button.setAttribute('aria-label', 'Copy code to clipboard');
    button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(code.textContent); button.textContent = 'Copied'; }
      catch { button.textContent = 'Select the code'; }
      setTimeout(() => { button.textContent = 'Copy'; }, 1600);
    });
    pre.prepend(button);
  });
}
