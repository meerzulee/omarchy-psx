# PS5 target — planned

This directory reserves the PS5 distribution boundary. There is no PS5 rootfs,
installer, launcher, kernel integration or hardware acceptance in this import.

Use a separately selected and validated `linux-psx` PS5 kernel target when one
exists, with its own loader, initramfs/firmware, module tree, installation and
recovery contract. Do not reuse PS4 labels, PCI IDs, boot-set hashes or FPKG
profiles as proof that they apply to PS5.

The kernel repository records pinned public PS5 community research in
`provenance/ps5-research.json` and `docs/UNIVERSAL-KERNEL.md`. Shared package and
desktop policy can be factored out after the actual PS5 requirements are known.
