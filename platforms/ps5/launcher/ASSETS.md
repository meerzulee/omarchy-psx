# Launcher appearance sources

The preview follows the accepted original PS4 launcher at
`omarchy-ps4/fpkg/preview/fable5.html`. Its appearance uses genuine Omarchy
v4.0.0 assets at commit `f0020448ca87329199de7cb12f2015ebc4a3e5e7`, the same
pin recorded by the historical PS4 launcher:

https://github.com/omacom/omarchy/tree/f0020448ca87329199de7cb12f2015ebc4a3e5e7

| Theme | Mode | Default wallpaper | Wallpaper count |
| --- | --- | --- | --- |
| Tokyo Night | Dark | `0-winding-road.jpg` | 3 |
| Last Horizon | Dark | `1-eyes-wide.jpg` | 4 |
| Lupine | Light | `01-cherry-blossom-bokeh.jpg` | 5 |
| Solitude | Dark | `1-on-pole.jpg` | 5 |

Palettes come from the pinned `themes/<theme>/colors.toml` files. The helper
generates `preview/assets/themes.js` from those values. The 17 wallpaper files
retain their source bytes; CSS applies the preview's readability overlays.
`default/plymouth/logo.png` supplies the original wordmark mask, tinted with the
selected palette. The original `default/fonts/omarchy/omarchy.ttf` icon font is
also retained; it is not a body typeface.

Typography follows the families selected by Omarchy's pinned
`default/fontconfig/conf.avail/50-omarchy.conf`: Liberation Sans for the
interface and JetBrainsMono Nerd Font for monospace details. The local web
fonts are unmodified Liberation Sans 2.1.5 Regular/Bold and JetBrainsMono Nerd
Font Regular from Nerd Fonts v3.5.0. These fonts come from their own upstream
releases, with their notices, rather than from the PS4's system SST fonts or
OpenOrbis's Gontserrat fallback.

`manifests/ps5-launcher-assets.json`, relative to the repository root, records
the source URLs, sizes, SHA256 identities, archive members and destinations.
`scripts/fetch-ps5-launcher-assets` materializes the ignored `preview/assets/`
directory; its `--check` mode verifies the complete local set offline. Asset
and font notices stay with the materialized files. Local font acquisition
details are recorded in ignored `cache/ps5-launcher-fonts/metadata.json`.

Only the theme ID persists in browser storage. Selecting a theme previews its
default wallpaper; Shuffle previews another image; Cancel restores the
pre-entry theme and wallpaper. Apply saves the theme, and reloading returns to
its default wallpaper. No fonts are installed on the host.

The historical wallpaper lineage remains in
`platforms/ps4/fpkg/ui-prototype/WALLPAPER-SOURCES.md`; acquired artwork and
fonts retain their original terms. This setup prepares a local browser preview,
not a packaged PS5 application or console payload.
