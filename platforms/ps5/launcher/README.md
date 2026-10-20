# Omarchy PS5 launcher preparation

The intended experience is a console home-screen entry, a controller-friendly
Omarchy screen, one deliberate launch action, and a library for the owner's
custom payloads. The local interface prototype is in `preview/index.html`.
It includes keyboard/gamepad navigation, appearance selection and local-file
inspection. It does not submit a payload, install an app or write console files.

The appearance follows the original PS4 launcher: **Tokyo Night, Last Horizon,
Lupine and Solitude**, with 17 original Omarchy wallpapers, the Omarchy wordmark
and fonts matching its configured families. Source pins and asset provenance
are described in [ASSETS.md](ASSETS.md).

From the repository root, prepare the local assets and serve the preview on
loopback. The first command downloads missing pinned assets; `--check` verifies
them offline without writing files:

```sh
python3 scripts/fetch-ps5-launcher-assets
python3 scripts/fetch-ps5-launcher-assets --check
python3 -m http.server 8765 --bind 127.0.0.1 --directory platforms/ps5/launcher/preview
```

Open this address in a browser; on macOS, run the command in another terminal:

http://127.0.0.1:8765/

```sh
open 'http://127.0.0.1:8765/'
```

Loopback serving provides a consistent browser context for local SHA256
inspection. Stop the server with Ctrl-C. No system fonts are installed.

Use arrow keys / D-pad to move, Enter / Cross to select, Escape / Circle to go
back, and O / F2 / Options to open Appearance. Theme and wallpaper changes
preview immediately. Apply remembers the theme; Cancel restores the preceding
appearance. Shuffle changes the current wallpaper, and each reload starts with
the saved theme's default wallpaper.

Add a local payload to inspect its name, size and SHA256 when browser
cryptography is available. Files stay on the local computer and entries last
for the current session. The Omarchy entry explains the unresolved 12.40 Linux
loader dependency.

## Package and runtime choice

A working jailbreak and arbitrary ELF delivery are assumed for this project.
These do not identify which installed native application/package path is
available. A PS4 OpenOrbis FPKG cannot be relabeled into a PS5 native app; its
graphics, controller, storage and GoldHEN transport interfaces are PS4-specific.
The frozen PS4 implementation is a design reference.

Public projects provide three useful, distinct implementation references:

| Route | What exists upstream | Status for this launcher |
| --- | --- | --- |
| Home-screen web app + existing `elfldr` | Launchpad selects ELF files and communicates with the loader's HTTP interface. Its companion installer adds a home-screen application. | Preferred first integration to investigate. Current prototype is local only; no transport or installer included. |
| Homebrew Launcher + `websrv` | Installed launcher entry opens a local web UI; homebrew bundles contain `eboot.elf`, `sce_sys/icon0.png` and optional `homebrew.js`. | Existing launch surface to evaluate separately on 12.40. |
| Native SDL2 application | Nativehbl demonstrates a controller UI and bootstrap using the `websrv` bigapp backend. | Possible later native front end; upstream explicitly requires the Homebrew Launcher base package. |

These references do not establish an installable **custom native PS5 FPKG on
12.40**. No `.pkg` is produced by this preparation. In particular, the Launchpad
installer writes console application directories; running it would be a
separate authorized hardware action, not a local preview step.

Launchpad's current upstream UI uses remote assets/catalogue services. A future
Omarchy integration should bundle its UI assets and select explicit local
payloads. The current preview has no external asset or network dependency.

## Runtime boundaries to implement after qualification

1. **Catalogue:** discover owner-supplied entries through the selected PS5
   runtime, record exact artifact identity, and distinguish a Linux loader from
   a general homebrew payload. Filename/header checks do not prove compatibility.
2. **Transport:** adapt to the already running loader's documented interface.
   The PS4 transport's port and single-write assumptions are not a PS5 contract.
   A submission result is not a successful boot result.
3. **Omarchy boot state:** consume a separately verified PS5 boot set and the
   compatibility/dependency record. Keep the 12.40 entry unavailable while the
   hypervisor or Linux handoff requirement remains unresolved.
4. **Installed entry/native UI:** qualify its own package format, base-app
   dependency and rendering lifecycle. Keep this independent of Linux support.

The established PS5 Linux loader documents etaHEN/kstuff incompatibility with
its rest-mode path. That warning applies to its supported older-firmware
implementation, not a demonstrated future 12.40 result. It is a reason to
evaluate the launcher in a plain ELF-loading environment first, rather than
assume a game-enabling runtime is a Linux prerequisite.

## Pinned source references

Runtime research snapshot: 2026-10-17. Machine-readable pins are in
`upstream.json`. No third-party launcher code or executable payload is included;
the separately acquired appearance assets have their own pinned manifest.

Launchpad / standard loader transport:
https://github.com/ps5-payload-dev/launchpad/tree/033d2a33df5beadbf3b7f9b80a4cae4369f1dca3
https://github.com/ps5-payload-dev/elfldr/tree/02cfe91eb3f9697787460ad77d73ff951f801f50

Homebrew web UI / package surface:
https://github.com/ps5-payload-dev/websrv/tree/7748df9d2a43822a5ebfda149f43d4f2696d640b

Native UI reference:
https://github.com/Rufidj/Nativehbl/tree/e9488102399de9546d13dd496694c74142abe49f

Existing Linux loader's runtime limitations:
https://github.com/ps5-linux/ps5-linux-loader/blob/64637c177eaed277fb6ccce394cbb29dd047b893/README.md

The next deliverable after UI review is a qualified PS5 runtime adapter and
package route. This document does not treat that future work as implemented.
