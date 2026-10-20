# Omarchy psX web manual

The website is generated from the fifteen numbered chapters and table of
contents in `../manual/`. Edit those Markdown files; the website supplies the
layout, navigation and local search. Research directories, experiment records
and other repository documents are not copied into the site.

## Build and preview

With Node.js 22 or newer, from this directory:

```sh
npm ci
npm run check
npm run dev
```

Open the printed loopback URL. The server binds only to `127.0.0.1`. Stop it
with Ctrl-C. After editing Markdown, CSS or JavaScript, run `npm run build`
again and refresh the page; the preview serves the rebuilt output.

`npm run check` validates chapter order, relative links, local anchors and
images without writing a build. `npm run build` writes the complete static
site to `dist/`, including search data, the manual's images and the project's
MIT license notice. The site needs
no application server, account, analytics service or remote content fetch.
Reading and navigation work without JavaScript; search and code copying are
progressive enhancements.

## Hosting

The generated directory can be served by any static host. No deployment is
performed by a build or preview. For hosting beneath a path, set `SITE_BASE`
at build time, including the leading and trailing slash:

```sh
SITE_BASE=/omarchy-psx/ npm run build
SITE_BASE=/omarchy-psx/ npm run preview
```

`SITE_URL=https://docs.example.org` optionally supplies the production origin
for canonical links and `sitemap.xml`. Leave it unset for local previews.
Never publish a preview's loopback address as the production site URL.

The chapter manifest in `build.mjs` is the publication allowlist. Links to
technical source documents resolve to GitHub; their contents are not bundled
or indexed. Linux psX remains the named and linked kernel project.

### Cloudflare production

The manual is hosted as static assets on the `omarchy-psx` Cloudflare Worker:

https://omarchy.mrz.sh/

The same deployment is also available at Cloudflare's standard Worker address
while a new custom-domain DNS record propagates:

https://omarchy-psx.meerzulee.workers.dev/

Downloads and release announcements link to the project's Telegram channel:

https://t.me/omarchy_psx

`wrangler.jsonc` records the account, custom domain and `dist/` asset directory.
Wrangler manages the custom domain's DNS record and HTTPS certificate. The
deployment contains only generated public documentation and assets; USB images,
research, logs, source files and local credentials are not uploaded. The large
USB image remains a separate download in the channel.

From this directory, with the intended Cloudflare account logged in:

```sh
npm ci
npx wrangler whoami
npm run deploy:check
npm run deploy
```

Both deployment commands run the manual's link checks and rebuild with the
production origin, generating canonical links, `sitemap.xml` and `robots.txt`.
`deploy:check` performs a local dry run. `deploy` publishes to the custom domain;
the ordinary build and preview commands remain local. There is no Git push in
this workflow. Wrangler is pinned locally and updated when its dependency
audit identifies security fixes. Its `.wrangler/` state is ignored by Git.

On a Mac with Homebrew libvips installed, use
`SHARP_IGNORE_GLOBAL_LIBVIPS=1 npm ci` if Sharp tries to build from source.
This lets Wrangler's dependency use its packaged native binary.

Cloudflare references:

https://developers.cloudflare.com/workers/static-assets/binding/

https://developers.cloudflare.com/workers/configuration/routing/custom-domains/

### Public content and browser security

The chapter manifest and explicit asset-copy list in `build.mjs` define what
is published. Search indexes only those chapters. The deployment has no
application API, database, uploaded credentials or secret bindings. Search runs
in the browser; it does not send search terms to an external service.

The build copies `_headers` into the output for Cloudflare to interpret.
Its content policy permits only the site's own scripts, styles, images and
search-index requests, blocks inline scripts and embedding, and disables
unneeded device permissions. Responses also disable MIME sniffing and outbound
referrer information, and enable HTTPS Strict Transport Security for the
individual site hostname. `_headers` itself is not publicly served.

Keep credentials out of manual text, screenshots and other publication inputs.
Local `.env*`, `.dev.vars*` and `.wrangler/` files are ignored by Git and are not
part of the asset-copy list. Git ignore rules do not hide a secret embedded in
a public chapter or image.

For a credential scan, install Gitleaks and run after building:

```sh
gitleaks dir dist --ignore-gitleaks-allow --redact=100 --no-banner
```

The website's publication boundary does not change the visibility of the
linked GitHub repositories or remove existing repository history.

## Design reference

The requested reference was the Omarchy site's manual structure: a chapter
sidebar, a readable article, and previous/contents/next navigation.

https://github.com/omacom/omarchy-site/blob/master/manual/index.html

Reference inspected at commit `e6ab10760cfabf6fb453bbc6844595a2d89cacd5`.
This site's template, CSS and browser code are original implementations under
the repository's MIT license. The wordmark retains Omarchy's canonical SVG
lettering and adds **PSX** in the same **Delta Corps Priest 1** style. The
combined mark, standalone PSX mark and ASCII lettering are reusable assets in
`assets/`; the favicon uses the canonical Omarchy O outline. The artwork scales
as SVG and uses the current theme's accent color without downloading a font.

See [the branding record](BRANDING.md) for source commits and adaptations.
The upstream MIT notice is retained in `assets/LICENSE-omarchy.txt` and copied
into the generated site. No upstream site code, web fonts or analytics are
bundled.
