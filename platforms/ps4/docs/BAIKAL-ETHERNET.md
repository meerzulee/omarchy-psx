> Imported PS4 history from `omarchy-ps4` on 2026-10-17. Paths and milestones below describe the original PS4 implementation and artifacts; they do not qualify a new Linux psX build or PS5. Use the [current migration guide](../../../docs/MIGRATION.md) for the active repository layout. Private network/host details are redacted.

# Baikal Ethernet development handoff

The private `6.18.44-ps4-baikal-mts2` kernel now runs the built-in Ethernet
adapter as `psx0` on the tested PS4 Slim/Baikal B1 console. EXP-20261017-016
verified modem DHCP, preferred wired IPv4, certificate-verified HTTPS,
independently hash-checked 4 MiB transfers in both directions and three normal
NetworkManager profile reconnects. The owner also confirmed normal use.
This is an optional development target; the standard release is unchanged.

The investigation and original PHY correction are documented in the sibling
[kernel bring-up record](https://github.com/meerzulee/linux-ps4/blob/386df1ad97d92defee1794bf961a0e2f5dc85a1b/docs/BAIKAL-ETHERNET-BRINGUP.md).
Curated hardware results and remaining qualifications belong in
[the experiment ledger](../experiments/SESSIONS.md), EXP016. Raw firmware and
private UART captures are not distribution inputs.

## Two separate fixes

The original transmit failure involved a missing native PHY prerequisite.
PS4-RE mappings and native initialization showed that MMD30:0147 bit4 should
be cleared. The measured handoff had `0010`; the narrow correction to `0000`
restored the native link indication. A fresh packet experiment then proved TX
completion, the independently captured nonce frame and its received reply.
Fresh DMA allocations also changed between those packet experiments, so this
does not prove the register bit was the sole cause of every earlier failure.

The first mts2 boot exposed a separate userspace startup bug. NetworkManager
tried to raise the interface while the driver's explicit gate was closed.
The helper later opened the gate, but merely restoring management did not
produce another link-UP request. The module remained healthy and unpublished;
the service's successful exit did not establish a working network device.

Package `omarchy-ps4-ethernet` version `0.1.1-1` fixes that ordering:

1. Verify the exact kernel/config/module/build identity, PCI owner and MAC.
2. Probe the module with the first-open gate closed; keep NM management and
   autoconnect blocked while loading the owned profile.
3. Open the gate once, verify the armed/unpublished report and issue one
   explicit `ip link set dev psx0 up` while NM remains blocked.
4. Verify healthy publication, administrative UP, polling, DMA bounds and the
   permanent module reference. A successful command alone is insufficient.
5. Return the interface to NM management/autoconnect; carrier and DHCP remain
   asynchronous, including an unplugged boot.

The same corrected first-open sequence worked on the current boot without
rebuilding the kernel or rebooting. The reviewed package is installed for
future boots; its unattended startup still needs confirmation on a later boot.
An uncertain or faulted first-open is never automatically repeated.

## Current layout and normal use

- Kernel source: sibling target `6.18-baikal-mts2`, its config and ordered patch
  series. Build with the existing OrbStack helper on macOS ARM64 or native
  `make TARGET=6.18-baikal-mts2` on Linux x86-64.
- Complete matching modules: `/usr/lib/modules/6.18.44-ps4-baikal-mts2/`.
  Preserve both earlier releases beside it for rollback.
- Activation package source: `packages/omarchy-ps4-ethernet/`. The package has
  no install-time activation hook. Its enabled unit is conditioned on the
  exact mts2 kernel and sealed candidate manifest.
- Candidate pins: root-owned mode0600
  `/etc/omarchy-ps4/ethernet-candidate.json`.
- Owned NM profile: `PS4Ethernet`, UUID
  `00000000-0000-4000-8000-000000000001`, inherited MAC preserved, IPv4 DHCP,
  route metric100 and IPv6 disabled. Wi-Fi remains metric600 for recovery.

The existing Omarchy launcher PKG boots the USB override. No launcher update
is needed for this kernel. Only FAT-root `bzImage` changed; initramfs, boot
arguments, VRAM file and original `release.json` were preserved. Separate
candidate receipts describe this intentional development override. See
[the USB contract](USB-PARTITIONED-DEVELOPMENT.md) for verified media/rollback.

Useful checks on the PS4:

```sh
uname -r
nmcli -f DEVICE,TYPE,STATE,CONNECTION device status
ip -4 route get 1.1.1.1
systemctl status omarchy-ps4-ethernet.service --no-pager
journalctl -b -u omarchy-ps4-ethernet.service --no-pager
```

A connected `PS4Ethernet`, an IPv4 address and a WAN route through `psx0`
establish the selected route. Check actual traffic separately. Ordinary profile
disconnect/reconnect uses:

```sh
sudo nmcli connection down PS4Ethernet
sudo nmcli connection up PS4Ethernet ifname psx0
```

The service is an initializer, not a network toggle. An already healthy
published driver makes its helper return without rearming or changing NM.

## Shareable terminal output

This prints link/counter evidence without MAC, IP, hostname or machine IDs.
Keep the actual error/drop counters in a screenshot:

```sh
python3 - <<'PY'
import json, os, subprocess
d = json.loads(subprocess.check_output(
    ["ip", "-j", "-s", "link", "show", "dev", "psx0"]))[0]
s = d.get("stats64") or d["stats"]
print("PS4 Linux — Ethernet")
print(f"Kernel: {os.uname().release}")
print(f"Link: {d['operstate']} | Carrier: {'UP' if 'LOWER_UP' in d['flags'] else 'DOWN'}")
for label, key in (("RX", "rx"), ("TX", "tx")):
    v = s[key]
    print(f"{label}: {v['bytes']/2**20:.1f} MiB | {v['packets']:,} packets | {v['errors']} errors | {v['dropped']} drops")
PY
```

Link/counters alone do not establish Internet access or reproducible support;
the independently verified transfers/TLS and qualified ledger supply that
additional evidence. For an ordinary `ip -s link` screenshot, redact both
`link/ether` and the MAC-derived `altname enx...`.

Change the hostname independently of networking, for example:

```sh
sudo hostnamectl set-hostname omarchy-ps4
hostnamectl --static
```

No reboot is needed; a new terminal refreshes the shell prompt.

## Lifecycle and remaining limits

The driver retains one hardware/DMA generation for the boot. Administrative
down/up joins CPU processing and preserves ring cursors/BQL; it does not
allocate another hardware generation. Published memory and code remain pinned.
Terminal faults stop irreversibly; safe DMA drain, unload, reset, suspend and
remove are not established. The current implementation is polled, uses MTU1500
with offloads disabled, and is tested using IPv4; the wired profile disables
IPv6. No universal PS4/PS5 support claim follows.

Normal NM profile-down kept IFF_UP during the observed three cycles. A separate
test helper incorrectly assumed setting unmanaged would remove the IPv4
address; that guard failed even though the driver's explicit DOWN and later
owned-profile UP succeeded with the same DMA generation and no driver fault.
That test remains inconclusive for its strict packet-gating criterion. The
future helper now disconnects and verifies the owned profile before disabling
management; that changed helper has host tests but was not rerun on hardware.

EXP016 observed the healthy engine beyond900 seconds from first known
publication, with the same DMA/refcount and further verified public HTTPS.
Wired SSH passed and the temporary Wi-Fi peer route was removed. Ethernet
remains enabled/preferred with Wi-Fi recovery available. Physical cable
recovery has no recorded operator result and remains pending.
Package0.1.1 automatic startup, repeatable cold boot, additional
consoles and unsupported lifecycle operations remain distinct acceptance work.
All source, artifacts and private records for this handoff remain local.
