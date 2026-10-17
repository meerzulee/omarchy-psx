# Baikal Ethernet boot activation candidate

This optional package activates only a separately installed and sealed
`6.18.44-ps4-baikal-mts2` continuous MTS module. It contains tools/templates,
not a kernel or module, and is not included in the production image by default.
The earlier bounded mts1 result does not establish this lifecycle's support.

The owner-approved installer must supply root:root mode0600
`/etc/omarchy-ps4/ethernet-candidate.json` with exactly these fields:

```json
{
  "schema": 1,
  "kernel_release": "6.18.44-ps4-baikal-mts2",
  "kernel_config_sha256": "<actual uncompressed /proc/config.gz SHA256>",
  "module_path": "/usr/lib/modules/6.18.44-ps4-baikal-mts2/kernel/drivers/net/ethernet/psx_mts_net.ko",
  "module_sha256": "<actual installed module SHA256>",
  "loaded_note_hex": "<complete .note.gnu.build-id bytes in hexadecimal>"
}
```

No placeholder is accepted. Before the fresh boot, the installer must also
render `PS4Ethernet.nmconnection.in` with the verified inherited MAC and stage
it as root:root0600 at
`/etc/NetworkManager/system-connections/PS4Ethernet.nmconnection`. Pre-staging
lets NetworkManager see the suitable owned profile before the device appears,
avoiding an automatically generated competing Wired connection. Existing
unrelated profiles are preserved; a competing compatible autoconnect profile
causes a refusal rather than deletion or modification.

Profile validation accepts NetworkManager's equivalent Ethernet alias, MAC
letter case, numeric timestamp, empty proxy section, and omission of the two
known defaults: `autoconnect=true` and `auto-negotiate=false`. UUID, filename,
interface, MAC-preserve policy, WOL-ignore policy, IP methods and metric remain
strict. NetworkManager1.58's keyfile writer skips default-valued properties;
the relevant connection/wired defaults are true/false respectively.

The installer enables
`omarchy-ps4-ethernet.service` for a future reviewed boot; package installation
does not enable/start the service. An old fallback kernel skips the unit by its
exact kernel-version condition. It runs after local filesystems and
NetworkManager, waits at most10 seconds for `baikal_pcie`, checks release,
configuration, module identity/path and an option-free modprobe plan, and loads
the module explicitly. It accepts only a LIVE, bound, gated/unpublished PROBED
state with the continuous contract (`continuous=1`, `lease_seconds=0`).

Before arming, it blocks device autoconnect, marks only `psx0` unmanaged, disables
that interface's IPv6, and creates or validates its own root0600
`PS4Ethernet.nmconnection`. It loads only that file, verifies its UUID/filename
and refuses competing compatible Ethernet autoconnect profiles without editing
them. The inherited hardware MAC is matched and preserved; the driver supplies
the same permanent MAC. The profile uses IPv4 DHCP, route metric100 (ahead of
the existing Wi-Fi metric600), and IPv6 disabled. Link speed/duplex and WOL are
left to the existing driver state; the profile does not request negotiation.

Only after profile load and the final guards does the helper write
`allow_open=1`. While NetworkManager remains unmanaged/autoconnect-disabled,
it performs exactly one explicit `ip link set dev psx0 up` with a25-second
command bound. It then verifies a healthy published continuous engine,
admin-up/poll enabled and exactly one permanent module reference before marking
`psx0` managed with device autoconnect enabled. Carrier may still be absent;
no carrier-up requirement or DHCP wait is introduced.

Version0.1.0 assumed NM would issue a fresh UP on management handoff. One boot
instead left the interface DOWN with its gate armed and no publication after
an earlier NM gate-closed UP failure. Its service exit0 was not Ethernet startup
acceptance. Version0.1.1 adds the explicit first open and positive publication
check; this correction still requires its own fresh-boot hardware result.
An IP-command exit0 alone is insufficient because the driver can return0 after
a terminal retained publication fault. No UP/gate retry or allowed1 recovery
path is added to the activator.

NetworkManager handles carrier, DHCP and later connection reopen asynchronously.
No DHCP lease or cable is required for service success. DNS changes follow only
this ordinary NetworkManager connection; no direct resolver, firewall, NAT,
Wi-Fi profile or global NetworkManager configuration edit is made.

A repeat start on the same healthy published continuous engine validates the
pins, retained resources and owned profile, then returns without rearming or
changing NetworkManager. A terminal fault, changed profile, wrong pin or
uncertain activation is refused for inspection. There is no ExecStop, unload,
reset, automatic recovery/retry or old-resource cleanup. Disabling this service
only prevents later boot activation; it does not stop an already published
engine. Kernel terminal-fault/shutdown retention remains the driver's policy.

Host-only tests:

```sh
./tests/baikal-ethernet-test
```

NetworkManager reference contracts (checked against1.58 source/API):

https://www.networkmanager.dev/docs/api/latest/nmcli.html
https://www.networkmanager.dev/docs/api/latest/nm-settings-nmcli.html
https://www.networkmanager.dev/docs/api/latest/nm-settings-keyfile.html
https://raw.githubusercontent.com/NetworkManager/NetworkManager/1.58.0/src/nmcli/connections.c
https://raw.githubusercontent.com/NetworkManager/NetworkManager/1.58.0/src/libnm-core-impl/nm-keyfile.c
https://raw.githubusercontent.com/NetworkManager/NetworkManager/1.58.0/src/libnm-core-impl/nm-setting-connection.c
https://raw.githubusercontent.com/NetworkManager/NetworkManager/1.58.0/src/libnm-core-impl/nm-setting-wired.c
