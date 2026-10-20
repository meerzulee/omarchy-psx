# Networking

NetworkManager runs the network, just like on any Omarchy machine. Click the network icon in the top bar to pick a Wi-Fi network or check your connection.

## Wi-Fi

The PS4's built-in Wi-Fi is a MediaTek MT7668. On the tested console it associated, got an address over DHCP, and carried SSH, DNS and verified HTTPS traffic. If `omarchy-ps4-status` says Wi-Fi is _ready_, choose a network from the top bar.

Linux psX kernels don't carry any device firmware, so with one of those kernels the Wi-Fi and Bluetooth firmware has to be in the initramfs before Linux mounts the USB drive. Our scripts download it from its public sources onto your own machine and add it for you. See [Kernels and Firmware](08-kernels-and-firmware.md#wi-fi-and-bluetooth-firmware).

## Ethernet

Native Baikal Ethernet is included in the `6.18.44-psx-ps4-baikal2` and `7.2.11-psx-ps4-baikal-native-dev1` targets. Functional observations come from the separate local builds described below. The kernel the v0.31 launcher carries predates it and has no built-in Ethernet.

There's nothing to set up. At boot, Linux loads the `psx_mts_net` driver, which creates an interface called `psx0`. NetworkManager's default wired profile brings it up, whether the cable was plugged in at boot or later, and the bar shows the Ethernet icon once it's connected.

Two boots of the native Ethernet patch set passed on our test console, one with the cable plugged in at launch and one without, including unplugging and replugging, two-way transfers, HTTPS and more than 15 minutes of traffic. That's good evidence, not a guarantee: other consoles, other network managers and repeated cold boots haven't been tested, and the published CI builds haven't been booted.

A few rules that come from the hardware:

- **Don't unload or reload the driver.** Once `psx0` has been brought up, the driver keeps its memory and state until the console powers off. After a terminal driver fault, power the console fully off before the next boot; do not reload or rearm it.
- **Keep the wired MAC address as it is.** The driver can't change it, so a NetworkManager profile that randomizes the wired MAC address fails to activate. Leave it on _preserve_.
- **Other network managers** need a configuration that names `psx0`; it doesn't match the usual `en*` or `eth*` patterns.

To keep Ethernet off for a boot, add one of these to the kernel command line:

- `psx_mts_net.autoarm=0` loads the driver but waits for an explicit go-ahead before first use.
- `modprobe.blacklist=psx_mts_net` doesn't load the driver at all.

To check that traffic really flows:

```bash
uname -r
nmcli device status
ip -4 route get 1.1.1.1
ip -s link show dev psx0
sudo cat /sys/module/psx_mts_net/parameters/report
curl --interface psx0 --noproxy '*' --fail --max-time 30 https://example.com/ -o /dev/null
ip -s link show dev psx0
```

A cable icon or an IP address alone doesn't prove much. A successful HTTPS request over `psx0` and counters that go up between the two `ip -s link` calls do. The driver's full story is in [Linux psX's Ethernet guide](https://github.com/meerzulee/linux-psx/blob/master/docs/ETHERNET.md).

_Redact MAC addresses, IP addresses and serial numbers before you post any of this output._

## Bluetooth

Bluetooth is switched on in owner-ready images, and its widget sits next to the network icon in the bar. On our test console, one Bluetooth speaker connected and played stereo audio with a Linux 7.2 development kernel. Reconnecting, staying paired across reboots and DualShock controllers haven't been tested yet.

## SSH and the firewall

SSH is off until you turn it on, and the PS4 kernels have no firewall. Both are covered in [First Boot](03-first-boot.md#ssh-stays-off) and [What's Different on PS4](05-whats-different-on-ps4.md#no-firewall).

<!-- manual-navigation -->

---

[← Previous](05-whats-different-on-ps4.md) · [Contents](README.md) · [Next →](07-storage.md)
