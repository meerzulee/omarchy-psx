# Orbis 12.02 kernel audio/HDMI findings — 2026-10-22

> **Static-analysis note.** This is not a hardware experiment and does not
> create or satisfy a `SESSIONS.md` acceptance entry. Native 48 kHz is still
> robotic; the 44.1 kHz PipeWire workaround remains active. No Linux patch or
> console action is implied by this document.

## Scope

The question was: what does the Orbis 12.02 kernel `aout` / `hdac` path do for
HDMI audio that the Linux 6.18 path does not, after application format,
channel count, AFMT, DTO, ACR, DP_SEC and bridge-register experiments all left
native 48 kHz robotic?

Artifacts:

- Orbis 12.02 retail kernel: `kernel1202.elf`, 20,080,104 bytes,
  SHA-256 `55b4948df94aee193ebeb653bd40aff55b3cf09ac7741f58f3dadc239b29a0a2`.
- IDA Pro 9.4.3 with Hex-Rays 9.4.0.260714; fresh analysis of
  `kernel1202.elf`, 17,135 functions.
- Existing ``fullkernel1202.i64`` was not used for decompilation: it has no
  function objects in the `aout`/`mixer`/`hdmi` ranges.
- Device/ioctl tables already in `references/ps4/ps4fw/`:
  `kernel_devices_1202.tsv`, `kernel_named_symbols.tsv`,
  `hdmi_ioctls_1202.tsv`.

## Bottom line

IDA confirms the Orbis `aout` device uses the standard OSS PCM ioctl set and
routes SPEED/SETFMT/CHANNELS/SETFRAGMENT through the PCM channel methods into
the `hdac` HDA driver. The strongest new HDMI-specific difference is that
Orbis `hdac` programs the HDMI converter with HDA verbs **0x70D**
(`SET_DIGI_CONVERT_1`) and **0xF0D** (`GET_DIGI_CONVERT_1`),
using a read-modify-write of the existing value. Linux 6.18's HDMI setup path
delegates to `snd_hda_codec_setup_stream` (the standard 0x706/0x200 verbs), and
the 6.18 HDMI/ATI HDMI code does not perform this DIGI_CONVERT_1 RMW in the
paths inspected.

**Correction:** `0x70D/0xF0D` are `AC_VERB_SET/GET_DIGI_CONVERT_1`, not
`SET/GET_HDMI_CHANNEL_STREAMID`. The HDMI channel stream ID is `0x706`, which
Linux already programs. The Orbis-specific operation is the DIGI_CONVERT_1
read/modify/write described below.

The 0x70D DIGI_CONVERT_1 write was implemented and tested in
EXP-20261022-064. It did not fix native 48 kHz: the RMW ran, but one
8-channel/48 kHz direct-ALSA clip remained robotic. The 44.1 kHz PipeWire
fallback remains clean. See “Hardware result” below.

The earlier `ORBIS_AUDIO_UPDATE_TICK_PARAMS = 0xC004505c` assumption is not
supported by the kernel handlers analysed here. The `aout` ioctl switch covers
only the standard `0xC0045002`–`0xC004500A` group; the `hdmi` device ioctl is
display-oriented and has no `0xC004505c` case. Treat the 0x5c tick-params path
as unresolved/userland until new evidence appears.

## Confirmed: `aout` ioctl mapping

`aout` device `d_ioctl` is `0xffffffff82752210`. Its two switches contain:

| ioctl | OSS meaning | `aout` case | Kernel path |
|---|---|---|---|
| `0xC0045002` | `SNDCTL_DSP_SPEED` | `3221508098` | `sub_FFFFFFFF827421E0` → `sub_FFFFFFFF82742000` |
| `0xC0045003` | `SNDCTL_DSP_STEREO` | `3221508099` | grouped at `LABEL_359` |
| `0xC0045004` | `SNDCTL_DSP_GETBLKSIZE` | `3221508100` | `sub_FFFFFFFF8274FDD0` |
| `0xC0045005` | `SNDCTL_DSP_SETFMT` | `3221508101` | `sub_FFFFFFFF827421A0` → `sub_FFFFFFFF82742000` |
| `0xC0045006` | `SNDCTL_DSP_CHANNELS` | `3221508102` | `sub_FFFFFFFF827491E0`, then `sub_FFFFFFFF827421A0` |
| `0xC0045007` | grouped | `3221508103` | grouped at `LABEL_359` |
| `0xC0045008` | grouped | `3221508104` | grouped at `LABEL_359` |
| `0xC0045009` | grouped | `3221508105` | grouped at `LABEL_359` |
| `0xC004500A` | `SNDCTL_DSP_SETFRAGMENT` | `3221508106` | `sub_FFFFFFFF82743A40` → `sub_FFFFFFFF82743130` |

The write-only variants `0x40045002`–`0x40045006` (decimal
`1074024450`–`1074024454`) are the other switch. No `0xC004505C` case appears
in either switch, and no full 32-bit `0xC004505C` immediate was found in the
`aout`/`mixer`/`hdmi` module ranges.

The source paths embedded in the kernel confirm the layers:

- `...\audioout\sound\pcm\dsp.c` for the `aout` dsp ioctl
- `...\audioout\snd_hda\hdac.c` for `hdac`
- `...\audioout\sound\pcm\sound.c` for the PCM core

## Confirmed: PCM → hdac dispatch

- `SNDCTL_DSP_SPEED` calls `sub_FFFFFFFF827421E0`, which calls
  `sub_FFFFFFFF82742000(a1, old_format, new_speed)`.
- `SETFMT` calls `sub_FFFFFFFF827421A0`, which calls
  `sub_FFFFFFFF82742000(a1, new_format, old_speed)`.
- `sub_FFFFFFFF82742000` selects the channel methods, applies the format/rate,
  then calls `sub_FFFFFFFF82743130` for the fragment defaults.
- `SETFRAGMENT` goes through `sub_FFFFFFFF82743A40` to
  `sub_FFFFFFFF82743130`.

The `hdac_channel` class is at `0xffffffff82eb8390` (class structure at
`0xffffffff83cd7a90`; method table at `0xffffffff83cd7b00`). Relevant methods:

| Role | Function | Notes |
|---|---|---|
| format validation | `sub_FFFFFFFF8273C150` | checks the format list at `a2+24`, stores `a2+100` |
| rate selection | `sub_FFFFFFFF8273C190` | selects from the list at `a2+168`; default **48000**, stores `a2+96` |
| set blocksize | `sub_FFFFFFFF8273C1E0` | calls `hdac_channel_setfragments`, returns `a2+252` |
| set fragments | `sub_FFFFFFFF8273C210` | `hdac_channel_setfragments`, logs to `hdac.c` |
| trigger | `sub_FFFFFFFF8273C390` | start calls `sub_FFFFFFFF8273A340`; stop calls `sub_FFFFFFFF8273A090` |
| get pointer | `sub_FFFFFFFF8273C410` | stream position |
| get buffer | `sub_FFFFFFFF8273C4D0` | returns `a2+16` |
| set parameter | `sub_FFFFFFFF8273C4E0` | case 2 calls `sub_FFFFFFFF8273C5F0` |
| set flags | `sub_FFFFFFFF8273C560` | handles the `*** no optical out ***` path |

## New candidate: HDA DIGI_CONVERT_1 (IEC 60958)

`sub_FFFFFFFF8273C5F0` is reached from the channel parameter setter
(`sub_FFFFFFFF8273C4E0`, case 2). It:

1. gets the codec address from the `hdac` softc and builds
   `codec_addr << 28`;
2. iterates the converter NID list at `a2+296`;
3. sends **`0xF0D` — `GET_DIGI_CONVERT_1`** to each converter NID;
4. preserves the returned low `0x6F` bits and ORs in `0x10` for `a3 == 1`
   or `0x80` for `a3 == 2`;
5. sends **`0x70D` — `SET_DIGI_CONVERT_1`** with that value, combined with
   the converter NID and codec address.

The command sender is `sub_FFFFFFFF8272F270`; the softc lock/assertion strings
are from `hdac.c` lines 4295–4328. The function stores the parameter in
`a2+268`. The `0x10` and `0x80` bits are `AC_DIG1_COPYRIGHT` and
`AC_DIG1_LEVEL` respectively; the `0x6F` mask preserves the remaining
DIGI_CONVERT_1 control bits. This is the per-converter IEC 60958 control RMW;
`0x706` is the separate HDMI channel stream ID, already programmed by the
generic setup.

### Linux 6.18 comparison

The exact 6.18 tree uses the reorganized HDA layout:

- `sound/hda/codecs/hdmi/hdmi.c`, `snd_hda_hdmi_setup_stream` (v6.18 line 718)
  calls `snd_hda_codec_setup_stream` (line 755).
- `sound/hda/codecs/hdmi/atihdmi.c`, `atihdmi_setup_stream` (line 466) also
  calls `snd_hda_hdmi_setup_stream`.
- Neither inspected HDMI file performs the `0x70D` /
  `AC_VERB_SET_DIGI_CONVERT_1` RMW for the ATI/AMD path.
- The generic setup path programs the converter with
  `AC_VERB_SET_CHANNEL_STREAMID` (`0x706`) and
  `AC_VERB_SET_STREAM_FORMAT` (`0x200`); `snd_hda_hdmi_setup_stream` reads
  `GET_DIGI_CONVERT_1` only for the Intel HSW `DIGI_CONVERT_3` workaround.

The exact 6.18.44 build tree should be re-checked at
`sound/hda/codecs/hdmi/{hdmi.c,atihdmi.c}` before patching, because the source
moved out of `sound/pci/hda/` in this kernel generation. If the DIGI_CONVERT_1
RMW is indeed absent, the minimal experiment is to add the Orbis-style
0xF0D/0x70D DIGI_CONVERT_1 RMW for the PS4 HDMI codec only, after the existing
0x706/0x200 setup.

## Hardware result — EXP-20261022-064

The 0x70D candidate was booted as
`7.2.11-psx-ps4-baikal-uvd-runtime-underscan-dev1-ps4hdmi70d`
(`bzImage` `8d88cdf3…`), using the v2 audio bootargs `6eeae7cd…`,
initramfs `cf2102f5…`, vram `4f71bb76…`, and 41 matching modules.

- The boot log confirms the RMW was active, e.g.
  `snd_hda_codec_atihdmi hdaudioC0D0: PS4 HDMI DIGI_CONVERT_1 nid=0x2
  old=0x211 new=0x11 fmt=0x37`.
- One 8-channel 48 kHz S32 WAV (`fc90e6f6…`) was played directly to
  `hw:0,3`; ALSA accepted S32_LE/8ch/48000, period 6000, buffer 24000;
  `aplay_rc=0`.
- The owner reported **still robotic/distorted**. The 0x70D DIGI_CONVERT_1
  RMW is therefore not sufficient. The remaining difference is below the
  codec, in the Orbis `aout`/bridge path.
- UART `EXP-20261022-064` completed. The playback slice also shows the
  expected `IRQ timing workaround ... bigger bdl_pos_adj`; that workaround was
  already tested in EXP058 without fixing 48 kHz.
- The 44.1 kHz PipeWire fallback remains the known-good state; no 44.1 path
  setting was changed. No native-48k acceptance is claimed.

### Static follow-up — converter sequence (2026-10-22)

Independent IDA verification of the read-only agent report
(`lab/audio-0x70d-20261022/AGENT-AOUT-ANALYSIS.md`) changes the interpretation
of the 0x70D-only result:

- Orbis `hdac` trigger start writes, in this order:
  **`0x200` → `0x70D` → `0x70E=0x79` → `0x706`** → RUN
  (IDA instructions at `0xffffffff8273A961`, `A9E1`, `AA47`, `AAC1`).
- Linux writes **`0x706` then `0x200`** (`snd_hda_codec_setup_stream`;
  `pcm_format_first=0`), and the EXP-064 patch appended only `0x70D` after
  that. Linux never writes `0x70E` (`AC_VERB_SET_DIGI_CONVERT_2`).
- Therefore the EXP-064 **0x70D-only** test did not replicate the Orbis
  converter sequence. It closes the 0x70D-only variant, not the full sequence.
- `0x70E=0x79` is the Orbis `AC_DIG2_CC` category-code field. Linux leaves the
  AFMT category at 0; this is a candidate only after the ordered sequence.
- The Orbis BDL is **2 × 8192 bytes**; Linux negotiated **4 × 192000 bytes**.
  This is a real timing difference but is not 48 kHz-specific.
- `0xC004505C` **is** handled by the `aout` driver
  (`sub_FFFFFFFF82744BE0`, `tick_get`), but it only caches rate/channel/width/
  block-size globals and writes no HDA or controller state. Direct ALSA
  bypasses it, so it is not the direct-ALSA 48 kHz cause. This corrects the
  earlier “absent” statement.
- The Orbis `aout`/`hdac` path has **no 48 kHz branch**; the rate table,
  `SDxFMT` and BDL mechanics are rate-agnostic. The remaining differences are
  the converter sequence above, the BDL geometry, and the codec/bridge
  response.

**Next single candidate:** the full ordered converter sequence, initially as a
cheap `hda-verb` `0x70E=0x79` pre-check during one 48 kHz clip, then the
decisive ordered kernel sequence. The BDL `2 × 8192` geometry is the next
variable if that is negative. Do not repeat the 0x70D-only or the other
already-negative guesses.

## Fragment/BDL path (secondary)

`sub_FFFFFFFF8273C210` (`hdac_channel_setfragments`) computes the block size
and count with:

- a 1024-byte alignment derived from `sub_FFFFFFFF8274FDA0` / gcd;
- block size floor 1024, clamped to half the available buffer;
- block count floor 2 and ceiling 256;
- a final `sub_FFFFFFFF8274F650(*a2, blkcnt, blksz)` and a
  `"%s: failed blksz=%u blkcnt=%u"` log on failure;
- stored copies at `a2+63` and `a2+62`.

The `aout` `SETFRAGMENT` path computes its own `blkcnt`/`blksz` from the OSS
integer (`v82=min(low16,0x10)`, `v86=max(4,v82)`, `blksz=1<<v86`, etc.) before
calling `sub_FFFFFFFF82743A40`. The `hdac` layer clamps the count to 256. If the
DIGI_CONVERT_1 experiment is negative, matching the Orbis `blkcnt`/`blksz`
values is the next lower-level variable; Linux `bdl_pos_adj` is not equivalent.

## Retracted/unresolved

- `0xC004505C` is handled by `aout` (`sub_FFFFFFFF82744BE0`, `tick_get`), but
  only caches rate/channel/width/block-size globals; it writes no HDA or
  controller state. Direct ALSA bypasses it. It is not the direct-ALSA 48 kHz
  cause. This corrects the earlier “absent” statement.
- The `hdmi` device `d_ioctl` (`0xffffffff828c8e70`) is the display HDMI
  handler (0x8d-style commands). It is not the audio path.
- The Ghidra result for `orbis_audiod.elf` remains valid: HDMI defaults to
  48 kHz and 8-channel LPCM, with 44.1 kHz conditional. EXP063 already tested
  8-channel 48 kHz on Linux and it remained robotic, so channel count is not
  the cause.

## Next actions

1. Decompile `sub_FFFFFFFF8273A340` and `sub_FFFFFFFF8273A090` (the `hdac`
   trigger start/stop) from the saved IDA database to identify the exact
   controller/BDL writes and the 0x200/0x706 converter setup.
2. Re-check the exact 6.18.44 `sound/hda/codecs/hdmi/{hdmi.c,atihdmi.c}` and
   `snd_hda_codec_setup_stream`; confirm that the DIGI_CONVERT_1 RMW is absent.
3. The 0x70D-only patch was prepared and tested in EXP-20261022-064; the
   native-48k result was negative. It did not replicate the Orbis converter
   sequence. Do not repeat the 0x70D-only experiment.
4. The next single candidate is the full ordered converter sequence:
   `0x200 -> 0x70D -> 0x70E=0x79 -> 0x706`, then RUN. A cheap `hda-verb`
   `0x70E=0x79` pre-check can precede the decisive ordered-kernel test; use one
   clip and keep the 44.1 kHz fallback.
5. If the ordered sequence is negative, the Orbis `2 x 8192` BDL geometry is
   the next variable; then the AFMT `AC_DIG2_CC`/category-code `0x79`. Do not
   repeat the already-negative 0x70D-only, 2ch/8ch, AFMT/DTO/ACR/DP_SEC or
   bridge-register guesses.

## Evidence

Local IDA reports (copied from the analysis host):

- `lab/hdmi-underscan-20261021-01/audio-calibration/ida-20261022/aout-device-handlers.txt`
  — `aout`/`mixer`/`hdmi` device decompilation, 2,447 lines.
- `lab/hdmi-underscan-20261021-01/audio-calibration/ida-20261022/pcm-dispatch.txt`
  — PCM speed/format/fragment dispatch, 743 lines.
- `lab/hdmi-underscan-20261021-01/audio-calibration/ida-20261022/hdac-channel-methods.txt`
  — `hdac_channel` class, methods and strings, 5,122 lines.
- `.../ida-20261022/scripts/ida_kernel.py`
- `.../ida-20261022/scripts/ida_hdac2.py`
- `.../ida-20261022/scripts/ida_hdac4.py`

The IDA database used for the method-table pass was
`/tmp/kernel1202_ida.i64` on the analysis host,
SHA-256 `629d8057a4faa83b3dd75638f040b6d8ed87843ab8614505c3f95c5a16247b48`.
It is derived from the kernel ELF above and is not a new firmware artifact.
