# PS5 target — dependency preparation

This directory owns PS5 distribution preparation. A separate kernel candidate
now lives in sibling `linux-psx`; the kernel and local RAM-only diagnostic
initramfs have been built and their contents verified. There is no completed
PS5 Omarchy rootfs or hardware acceptance.

The original PS5 on firmware **12.40** is the current preparation target.
Jailbreak and arbitrary ELF delivery are assumed working. The reviewed public
hypervisor and Linux loader implementations do not establish 12.40 support.
See [BOOT-DEPENDENCIES.md](BOOT-DEPENDENCIES.md) for pinned inputs, the artifact
contract and remaining blockers. The preparation tools fetch text references
and inspect files locally; they do not create or send a console payload.

[Launcher preparation](launcher/README.md) includes an offline controller UI
preview and research into PS5 home-screen/package routes. Native FPKG execution
and the Linux handoff remain separate unqualified dependencies on 12.40.

[REA findings](REA-FINDINGS.md) record the bounded IDA investigation of the
supplied ELF, including its missing 12.40 selector and warning fall-through.

From the repository root:

```sh
python3 scripts/fetch-ps5-references
python3 scripts/check-ps5-compatibility --validate-manifest
python3 scripts/check-ps5-compatibility --firmware 12.40 --sources cache/ps5-references
```

The last command intentionally returns **2** while the recorded dependencies
are unresolved. Exit 0 from manifest validation means valid metadata, not a
working boot path. No firmware offsets or compatibility overrides are supplied.

The `linux-psx` development target `7.2-ps5` selects the pinned community PS5
patch on Linux 7.2.3, with its own loader, initramfs/firmware, module tree, installation and
recovery contract. Do not reuse PS4 labels, PCI IDs, boot-set hashes or FPKG
profiles as proof that they apply to PS5.

The kernel repository records the candidate in `provenance/7.2-ps5.json` and
`docs/PS5.md`. [FIRST-BOOT.md](FIRST-BOOT.md) describes diagnostic preparation
and the remaining path to an Omarchy desktop.
