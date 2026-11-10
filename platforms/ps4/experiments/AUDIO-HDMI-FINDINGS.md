# PS4 HDMI audio at 48 kHz: findings

Recorded 2026-10-22. Reworded for publication 2026-11-10.

> This is an analysis note. The hardware results it cites are recorded in
> `SESSIONS.md`. Native 48 kHz was still robotic when this was written, and
> 44.1 kHz through PipeWire remained the working fallback.

What this note says about the console's own software comes from studying its
12.02 audio path, so that Linux can drive the same hardware. It is written in
our own words and reproduces no Sony code, symbols or strings.

## Question

Application format, channel count, AFMT, DTO, ACR, DP_SEC and bridge-register
experiments all left native 48 kHz robotic. What does the console's own audio
path do that Linux 6.18 does not?

## Result

- The console uses the standard OSS-style controls for rate, format, channels
  and fragments, routed through a PCM layer into an HDA driver.
- That path has no 48 kHz branch. Its rate table, stream format and buffer
  handling do not depend on the rate.
- HDMI defaults to 48 kHz, 8-channel LPCM. 44.1 kHz is conditional.
- The differences left are the order of the converter setup, the buffer
  geometry, and how the codec and bridge respond.

## Converter setup

| Path | Order of the verbs |
|---|---|
| Console | `0x200` stream format, `0x70D` DIGI_CONVERT_1, `0x70E` = `0x79` DIGI_CONVERT_2, `0x706` channel and stream ID, then RUN |
| Linux 6.18 | `0x706` channel and stream ID, then `0x200` stream format. It never writes `0x70E`. |

`0x70D` and `0xF0D` are the set and get forms of DIGI_CONVERT_1. They are not
the HDMI stream ID, which is `0x706`.

The console updates DIGI_CONVERT_1 as a read-modify-write on each converter. It
reads `0xF0D`, keeps the bits in mask `0x6F`, sets `0x10` (`AC_DIG1_COPYRIGHT`)
or `0x80` (`AC_DIG1_LEVEL`), and writes `0x70D`. `0x70E` = `0x79` is the
`AC_DIG2_CC` category-code field, which Linux leaves at 0 in AFMT.

In Linux 6.18, `snd_hda_hdmi_setup_stream` in `sound/hda/codecs/hdmi/hdmi.c` and
`atihdmi_setup_stream` in `atihdmi.c` end up in `snd_hda_codec_setup_stream`,
which writes only `0x706` and `0x200`. Neither performs this read-modify-write
on the ATI/AMD path. `snd_hda_hdmi_setup_stream` reads `GET_DIGI_CONVERT_1` only
for an Intel workaround. Check the exact kernel tree again before patching.

## Hardware result: `EXP-20261022-064`

The `0x70D` change alone was built as
`7.2.11-psx-ps4-baikal-uvd-runtime-underscan-dev1-ps4hdmi70d` and booted.

- The log confirmed that the read-modify-write ran:
  `PS4 HDMI DIGI_CONVERT_1 nid=0x2 old=0x211 new=0x11 fmt=0x37`.
- One 8-channel 48 kHz S32 WAV played directly to `hw:0,3`. ALSA accepted
  S32_LE, 8 channels, 48000 Hz, period 6000, buffer 24000.
- The owner reported it was still robotic. The UART session completed.
- The log also showed the known `bdl_pos_adj` IRQ timing workaround, which had
  already failed to fix 48 kHz in an earlier test.

This closes the `0x70D`-only variant. It did not reproduce the console's full
converter order, so the full order is still untested.

`EXP-20261022-063` already played 8-channel 48 kHz on Linux and stayed robotic,
so channel count is not the cause.

## Other differences checked

- **Buffer geometry.** The console uses 2 buffers of 8192 bytes. Linux negotiated
  4 buffers of 192000 bytes. This is a real timing difference, but it is not
  specific to 48 kHz.
- **Block sizing.** The console aligns blocks to 1024 bytes with a floor of 1024,
  caps the block at half the buffer, and allows 2 to 256 blocks. Linux
  `bdl_pos_adj` is not equivalent to this.
- **Tick parameters.** The console's tick-parameters ioctl only caches rate,
  channel, width and block size. It writes no HDA or controller state, and direct
  ALSA playback does not go through it, so it cannot explain the direct-ALSA
  result.
- **The HDMI display device.** Its control path is for display and is not part of
  the audio path.

## Next steps

Change one variable at a time, use one clip per test, and keep the 44.1 kHz
fallback.

1. Run a quick `hda-verb` pre-check of `0x70E` = `0x79` during one 48 kHz clip.
2. Run the full ordered kernel sequence: `0x200`, `0x70D`, `0x70E` = `0x79`,
   `0x706`, then RUN.
3. If that fails, match the 2 x 8192 buffer geometry.
4. If that fails, try the `AC_DIG2_CC` category code `0x79` in AFMT.

Do not repeat the `0x70D`-only test, the 2-channel or 8-channel comparisons, or
the AFMT, DTO, ACR, DP_SEC and bridge-register guesses.
