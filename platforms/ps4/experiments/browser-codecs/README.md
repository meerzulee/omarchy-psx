# PS4 browser codec policy

The owner's YouTube stream reported1920×1080@30 with`av01` video and Opus
audio. Liverpool's experimental UVD path exposes AVC/H.264, not AV1 or VP9.
Installing Mesa does not make those codecs hardware-decodable. Earlier exact
1080p30 AVC tests qualify the recorded FFmpeg/mpv path, not browser playback.

The owner requests compatible codecs in both browsers. The private console
installation uses unmodified upstream **h264ify**: Chromium2.0.1, ManifestV3,
at a full source commit, and the Mozilla-distributed Firefox1.1.0 XPI.
Versions, URLs, hashes and the Firefox add-on ID are in`upstreams.json`.
Retain upstream's MIT license. Generated downloads are external artifacts;
no XPI, source archive or browser profile belongs in Git.

Chromium loads the verified unpacked source through its existing
`--load-extension` list. Existing extensions and`--disable-gpu` are preserved.
Firefox's merged system policy installs the pinned local XPI for every
profile, disables updates only for that add-on and locks AV1 off. The policy
fragment is`firefox-policy.json`; merge its keys with existing policies rather
than replacing unrelated configuration. Firefox signature verification is
unchanged. The XPI retains its signature entries and is accepted or rejected
by Firefox itself.

h264ify filters YouTube's codec capability queries to prefer AVC. It is not a
transcoder, decoder implementation or hardware-acceleration switch. Audio
format may change with the selected stream. Resolutions without an AVC stream
will be unavailable. Restart the browser and reload the video; Stats for nerds
must report`avc1`, not`av01` or`vp09`. Do not promise1080p60 or4K playback.

EXP027's separate isolated Chromium VAAPI attempt reaches5UVD completions
then CS rejection(-28) aborts its GPU process. No terminal kernel marker is
observed; normal browser acceleration is left unchanged. A later headless
policy check on the actual YouTube origin allows AVC and rejects AV1/VP9 in
Chromium. A corrected Firefox observer confirms the same filter on the actual
YouTube origin, with the signed add-on active. The owner later reports
`avc1.640028`/`mp4a.40.2`; playback still lags on the subsequently faulted
CarChase boot. The session ledger preserves the initial observer failures and
the corrected checks. Codec selection alone does not qualify browser UVD.

Keep pre-install Chromium flags and Firefox policy copies. Rollback restores
those configuration files and removes only this installation's extension
references. Preserve browser profiles, history and existing extensions; do not
disable signatures, reset the GPU or enable distribution updates.
