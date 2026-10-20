# Contributing

Omarchy psX moves forward one tested change at a time, and there's room to help with code, documentation and, above all, careful hardware reports.

## Ideas, bugs and questions

Open an issue on [Omarchy psX](https://github.com/meerzulee/omarchy-psx/issues) for anything about the desktop, packages, the launcher, installation or these docs. Kernel and driver problems belong in [Linux psX](https://github.com/meerzulee/linux-psx/issues).

A useful report includes:

- your console model and southbridge,
- the launcher version and `uname -r`,
- what you did, what you expected and what happened,
- a short, relevant excerpt from `journalctl -b` or `omarchy-ps4-status`.

_Before you post, remove serial numbers, MAC and IP addresses, usernames and anything else that identifies your console. Never upload firmware, PS4 system software, keys, launcher packages, or raw UART and network captures._

## Changing the source

- Run `make check` before you send a change. The tests are synthetic: they never touch real devices, storage or the network.
- For manual or website changes, also run `npm ci`, `npm run check` and `npm run build` from `website/`. The site build checks chapter links and anchors before exporting the web docs.
- Keep kernel work in Linux psX. Omarchy psX consumes its kernels; it doesn't carry a kernel tree.
- Keep the deployed names as they are. Package names like `omarchy-ps4`, the `OMARCHY-PS4` drive label and the launcher's boot parameters are interfaces that existing installs rely on.
- When you bring in someone else's code, keep their copyright and license notices, and record where it came from in `provenance/`.
- In public documentation, describe reviewed private findings as **private hardware research**. Keep private tool names, repository paths, raw dumps and access details in local notes. Preserve attribution and license notices for imported code.

## Testing on real hardware

This is where the project needs the most help, and where it's strictest. A claim only counts when it comes from a recorded experiment on a real console:

1. **Give it an ID** like `EXP-20261019-001`, with one question, the evidence you expect, a timeout and a safe way back.
2. **Capture the console's UART continuously**, and open one bounded session for the whole experiment. A logger restart in the middle makes that session invalid.
3. **Change one thing.** Setup and cleanup can be grouped, but each experiment tests a single variable.
4. **Stop when the question is answered**, or as soon as something breaks badly. Then write down one clear result: pass, degraded, fail, inconclusive or blocked.
5. **Don't keep retrying.** If the same failure happens three times without new evidence, stop, record it and step back a layer.

A successful boot once is evidence, not support. Promotion to "working" takes repeated passes. And a green build, an installed package or a clean test suite is never a substitute for watching the real console.

The tooling helps: from `platforms/ps4/`, `./bin/omarchy-ps4-probe --experiment NAME` collects a diagnostic snapshot, and `./bin/omarchy-ps4-compare` compares two runs. Start each write-up from [the experiment template](../platforms/ps4/experiments/TEMPLATE.md), and read [the development mode rules](../platforms/ps4/docs/DEVELOPMENT-MODE.md) first. The curated history of every PS4 experiment is in [the session ledger](../platforms/ps4/experiments/SESSIONS.md). Raw captures stay on your own machine.

_Only test on a console you own, and only write to storage after you've identified the exact drive and confirmed it._

## Licenses

Original Omarchy psX code and documentation use the [MIT License](../LICENSE). Linux psX kernel work stays under GPLv2. Upstream Omarchy, the PS4 Linux loader and every other component keep their own licenses and notices; the launcher's attributions are in [its credits](../platforms/ps4/fpkg/CREDITS.md) and [third-party notes](../platforms/ps4/fpkg/THIRD_PARTY.md). See the [legal notice](15-legal-notice.md).

<!-- manual-navigation -->

---

[← Previous](13-building-from-source.md) · [Contents](README.md) · [Next →](15-legal-notice.md)
