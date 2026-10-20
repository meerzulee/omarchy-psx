#!/usr/bin/env python3
"""Paused, monitored PS4 Mesa/UVD demo. Default is a CPU-only preflight."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import socket
import subprocess
import sys
import time

MPV = Path('/usr/bin/mpv')
MPV_SHA256 = '3d4a55ab1d24f8da84e7e0a0e41d0a436dda6ea65e16ccb279599b184ecabab3'
FENCE = '/sys/kernel/debug/dri/0/amdgpu_fence_info'
PROPERTIES = ('hwdec-current', 'video-codec', 'video-params', 'current-vo',
              'vo-configured', 'pause', 'time-pos', 'duration', 'container-fps',
              'estimated-vf-fps', 'frame-drop-count', 'decoder-frame-drop-count')
TERMINAL = re.compile(r'failed to (?:end|start|decode) picture|\bdecode error\s*[:!]|'
    r'error (?:while )?decoding|hardware accelerator failed|hardware decoding failed|video decoding failed|'
    r'failed to (?:submit|initiali[sz]e.*(?:vaapi|video))|'
    r'amdgpu:\s*(?:The\s+)?CS\s+(?:has\s+been\s+)?rejected[^\n]*\(-28\)|'
    r'DRM_IOCTL_AMDGPU_CS.*failed|(?:amdgpu|ps4[_ -]?uvd).*?(?:fault|timeout|failed)|'
    r'vaapi.*?(?:error|failed)|gpu reset|segmentation fault|\bfatal (?:error|signal)\b', re.I)



def single_hwdec_thread(log_text):
    """Require the actual initialization request, not just an argv option."""
    requests = re.findall(r'\bRequesting\s+(\d+)\s+threads?\s+for\s+decoding\b', log_text, re.I)
    if any(int(value) != 1 for value in requests):
        raise RuntimeError('mpv requested multiple/automatic decoder threads: ' + ', '.join(requests))
    return bool(requests)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def parse_fence(text):
    blocks = re.findall(r'^--- ring \d+ \(ps4_uvd\) ---\s*\n(.*?)(?=^--- ring |\Z)', text, re.M | re.S)
    if len(blocks) != 1:
        raise RuntimeError('Expected exactly one ps4_uvd fence block')
    def counter(name):
        hits = re.findall(r'^' + name + r'\s+(0x[0-9a-fA-F]+)\s*$', blocks[0], re.M)
        if len(hits) != 1:
            raise RuntimeError('Missing/ambiguous UVD counter: ' + name)
        return int(hits[0], 16)
    completed, emitted = counter('Last signaled fence'), counter('Last emitted')
    if completed > emitted:
        raise RuntimeError('UVD completed counter exceeds emitted counter')
    return {'completed': completed, 'emitted': emitted}


def read_fence():
    # This debugfs read processes real fence writeback; it is run-only, never preflight.
    r = subprocess.run(['/usr/bin/sudo', '-n', '/usr/bin/cat', FENCE],
                       capture_output=True, text=True, timeout=2, check=True)
    return parse_fence(r.stdout), r.stdout


class IPC:
    def __init__(self, path):
        self.sock = socket.socket(socket.AF_UNIX)
        self.sock.settimeout(2)
        self.sock.connect(str(path))
        self.stream = self.sock.makefile('rb')
        self.serial = 0

    def call(self, *command, optional=False):
        self.serial += 1
        self.sock.sendall((json.dumps({'command': list(command), 'request_id': self.serial}) + '\n').encode())
        while True:
            raw = self.stream.readline()
            if not raw:
                raise RuntimeError('mpv IPC closed')
            msg = json.loads(raw)
            if msg.get('event') == 'end-file' and msg.get('reason') == 'error':
                raise RuntimeError('mpv end-file error: ' + str(msg))
            if msg.get('request_id') == self.serial:
                if msg.get('error') != 'success':
                    if optional:
                        return None
                    raise RuntimeError('mpv IPC failed: ' + str(msg))
                return msg.get('data')

    def snapshot(self):
        return {name: self.call('get_property', name, optional=True) for name in PROPERTIES}

    def close(self):
        self.stream.close()
        self.sock.close()


def gate(s, initial=False):
    if s.get('hwdec-current') != 'vaapi-copy':
        raise RuntimeError('Hardware decoder is not vaapi-copy')
    vp = s.get('video-params') or {}
    if (vp.get('w'), vp.get('h')) not in ((1280, 720), (1920, 1080)):
        raise RuntimeError('Unexpected decoded dimensions')
    if s.get('current-vo') != 'gpu' or s.get('vo-configured') is not True:
        raise RuntimeError('GPU video output is not configured')
    if not re.search(r'h\.?264|avc', str(s.get('video-codec')), re.I):
        raise RuntimeError('Decoder codec is not AVC')
    if not number(s.get('duration')) or s['duration'] <= 0:
        raise RuntimeError('Missing positive clip duration')
    if not number(s.get('time-pos')):
        raise RuntimeError('Playback time is unavailable')
    for key in ('frame-drop-count', 'decoder-frame-drop-count'):
        if not number(s.get(key)) or s[key] < 0:
            raise RuntimeError('Unavailable drop counter: ' + key)
    if initial and s.get('pause') is not True:
        raise RuntimeError('Player did not start paused')
    if not initial and s.get('pause') is not False:
        raise RuntimeError('Unexpected playback pause')


class Progress:
    def __init__(self, duration, position, fence, now):
        self.duration, self.position = duration, position
        self.wraps = 0
        self.completed = fence['completed']
        self.emitted = fence['emitted']
        self.last_progress = now
        self.clean = True
        self.samples = collections.deque([(now, position)], maxlen=6)

    def update(self, s, fence, now):
        gate(s)
        if abs(s['duration'] - self.duration) > .1:
            raise RuntimeError('Clip duration changed')
        pos = s['time-pos']
        if pos < self.position - .5:
            if self.position < .75 * self.duration or pos > .25 * self.duration:
                raise RuntimeError('Unexpected seek/discontinuous playback time')
            self.wraps += 1
        self.position = pos
        if fence['completed'] < self.completed or fence['emitted'] < self.emitted:
            raise RuntimeError('UVD fence counters went backwards')
        delta = fence['completed'] - self.completed
        if delta:
            self.last_progress = now
        if now - self.last_progress >= 10:
            raise RuntimeError('UVD completion has not advanced for 10 seconds')
        self.completed, self.emitted = fence['completed'], fence['emitted']
        self.clean &= s['frame-drop-count'] == 0 and s['decoder-frame-drop-count'] == 0
        self.samples.append((now, self.wraps * self.duration + pos))
        old_t, old_pos = self.samples[0]
        speed = (self.samples[-1][1] - old_pos) / (now - old_t) if now > old_t else None
        return {'completed_passes': self.wraps, 'current_pass': self.wraps + 1,
                'fence_completed_delta': delta, 'pts_wall_speed': speed,
                'clean_since_start': self.clean}


def playback_args(clip, output):
    return [str(MPV), '--no-config', '--no-terminal', '--load-scripts=no',
            '--osc=no', '--input-conf=/dev/null', '--input-default-bindings=no',
            '--input-builtin-bindings=no', '--input-vo-keyboard=no', '--input-terminal=no',
            '--input-cursor=no', '--input-gamepad=no', '--cursor-autohide=always',
            '--no-audio', '--hwdec=vaapi-copy', '--hwdec-codecs=h264',
            '--hwdec-software-fallback=no', '--vd-lavc-threads=1', '--hwdec-threads=1',
            '--vo=gpu', '--gpu-api=opengl', '--gpu-context=wayland',
            '--fullscreen', '--force-window=yes', '--pause=yes', '--loop-file=inf',
            '--keep-open=no', '--resume-playback=no', '--start=0',
            '--osd-level=0', '--osd-bar=no', '--osd-font-size=22',
            '--title=PS4 UVD | live hardware decode',
            '--input-ipc-server=' + str(output / 'ipc.sock'),
            '--log-file=' + str(output / 'mpv.log'), '--msg-level=all=info',
            '--', str(clip)]


def mapped_libraries(pid, root, output):
    text = Path(f'/proc/{pid}/maps').read_text()
    (output / 'mpv.maps').write_text(text)
    decode = lambda value: re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), value)
    paths = {decode(line.split(None, 5)[5]) for line in text.splitlines()
             if len(line.split(None, 5)) == 6 and line.split(None, 5)[5].startswith('/')}
    candidate = {p: digest(p) for p in sorted(paths) if p.startswith(str(root) + '/') and '.so' in p}
    required = ('libEGL_mesa.so', 'libgallium-', 'libvulkan_radeon')
    # Vulkan is not part of this OpenGL workload; do not require a RADV mapping.
    for name in required[:2]:
        if not any(name in p for p in candidate):
            raise RuntimeError('Candidate library not mapped: ' + name)
    if not any('radeonsi_drv_video' in p or 'libgallium-' in p for p in candidate):
        raise RuntimeError('Candidate video driver not mapped')
    # A same-name system Mesa library would invalidate the process-local comparison.
    for p in paths:
        if any(x in Path(p).name for x in ('libEGL_mesa', 'libGLX_mesa', 'libgallium-', 'libgbm', 'dri_gbm', 'libdril', 'radeonsi_drv_video')) and not p.startswith(str(root) + '/'):
            raise RuntimeError('System Mesa library mixed into candidate process: ' + p)
    pins = json.loads((root / 'MESA-PSX-CANDIDATE.json').read_text())['files']
    for path, sha in candidate.items():
        relative = str(Path(path).resolve(strict=True).relative_to(root))
        if pins.get(relative, {}).get('sha256') != sha:
            raise RuntimeError('Mapped candidate library differs from manifest: ' + path)
    save(output / 'LIBRARIES.json', candidate)
    return candidate


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'mesa-root', 'clip'):
        ap.add_argument('--' + name, type=Path, required=True)
    for name in ('manifest-sha256', 'clip-sha256', 'boot-id', 'release'):
        ap.add_argument('--' + name, required=True)
    ap.add_argument('--run', action='store_true', help='Launch only inside the authorized UART experiment')
    args = ap.parse_args()
    if sys.platform != 'linux' or platform.machine() != 'x86_64' or os.geteuid() == 0:
        ap.error('Run as the normal Linux x86_64 desktop user')
    here = Path(__file__).resolve().parent
    root, clip, output = args.mesa_root.resolve(strict=True), args.clip.resolve(strict=True), args.output.absolute()
    if output.exists() or len(os.fsencode(str(output / 'ipc.sock'))) >= 104:
        ap.error('Output must be fresh and its IPC path shorter than 104 bytes')
    if platform.release() != args.release or Path('/proc/sys/kernel/random/boot_id').read_text().strip() != args.boot_id:
        ap.error('Kernel release/boot ID mismatch')
    if digest(MPV) != MPV_SHA256 or digest(clip) != args.clip_sha256:
        ap.error('mpv or clip digest mismatch')
    wrapper = [sys.executable, str(here / 'with-mesa.py'), '--root', str(root),
               '--expected-manifest-sha256', args.manifest_sha256]
    verified = subprocess.run([*wrapper, '--verify-only'], capture_output=True, text=True, check=True)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    command = [*wrapper, '--', *playback_args(clip, output)]
    # Pinned mpv itself confirms option and property names without opening any media/device.
    options = subprocess.run([str(MPV), '--no-config', '--list-options'], capture_output=True, text=True, check=True)
    properties = subprocess.run([str(MPV), '--no-config', '--list-properties'], capture_output=True, text=True, check=True)
    (output / 'mpv-options.txt').write_text(options.stdout)
    (output / 'mpv-properties.txt').write_text(properties.stdout)
    names = {x.lstrip('-').split('=', 1)[0] for x in playback_args(clip, output)[1:-2] if x.startswith('--')}
    # --no-X is an alias for boolean option X.
    for name in names:
        key = name[3:] if name.startswith('no-') else name
        if not re.search(r'(?m)^\s*--' + re.escape(key) + r'(?:\s|$)', options.stdout):
            raise RuntimeError('Pinned mpv does not list option: ' + name)
    save(output / 'PREFLIGHT.json', {'argv': command, 'mpv_sha256': MPV_SHA256,
        'clip_sha256': args.clip_sha256, 'manifest_sha256': args.manifest_sha256,
        'boot_id': args.boot_id, 'release': args.release, 'verified': json.loads(verified.stdout),
        'run_requested': args.run, 'supervisor_sha256': digest(__file__)})
    if not args.run:
        print(output / 'PREFLIGHT.json')
        return 0
    if not os.environ.get('WAYLAND_DISPLAY') or not os.environ.get('XDG_RUNTIME_DIR'):
        raise RuntimeError('A published native Wayland session environment is required')
    initial_fence, raw = read_fence()
    (output / 'fence-before.txt').write_text(raw)
    if initial_fence['completed'] != initial_fence['emitted']:
        raise RuntimeError('UVD ring is not idle before demo')
    stopping = {'reason': None}
    def stop(signum, frame):
        stopping['reason'] = 'operator signal ' + str(signum)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    ipc = None
    child = None
    reason = 'unknown'
    try:
        with (output / 'stdout.txt').open('xb') as stdout, (output / 'stderr.txt').open('xb') as stderr:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True)
        save(output / 'PROCESS.json', {'supervisor_pid': os.getpid(), 'mpv_pid': child.pid,
             'ipc_socket': str(output / 'ipc.sock'), 'stop_command': 'kill -TERM ' + str(os.getpid()), 'argv': command})
        (output / 'STOP.txt').write_text('kill -TERM ' + str(os.getpid()) + '\n')
        deadline = time.monotonic() + 20
        while not (output / 'ipc.sock').exists():
            if child.poll() is not None or time.monotonic() >= deadline or stopping['reason']:
                raise RuntimeError('Player initialization failed/stopped before IPC')
            time.sleep(.1)
        ipc = IPC(output / 'ipc.sock')
        while True:
            initialization_log = ''
            for name in ('mpv.log', 'stdout.txt', 'stderr.txt'):
                path = output / name
                if path.exists():
                    text = path.read_text(errors='replace')
                    if name == 'mpv.log':
                        initialization_log = text
                    match = TERMINAL.search(text)
                    if match:
                        raise RuntimeError('Terminal initialization ' + name + ': ' + match.group(0))
            threads_confirmed = single_hwdec_thread(initialization_log)
            initial = ipc.snapshot()
            if stopping['reason'] or time.monotonic() >= deadline:
                raise RuntimeError('Player initialization stopped or exceeded 20 seconds')
            if initial.get('hwdec-current') not in (None, 'vaapi-copy'):
                raise RuntimeError('Initialization selected a different hardware decoder')
            required = ('hwdec-current', 'video-params', 'current-vo', 'duration',
                        'time-pos', 'video-codec', 'frame-drop-count', 'decoder-frame-drop-count')
            if threads_confirmed and initial.get('vo-configured') is True and all(initial.get(k) is not None for k in required):
                gate(initial, initial=True)
                break
            time.sleep(.1)
        save(output / 'INITIAL.json', initial)
        mapped_libraries(child.pid, root, output)
        paused_fence, raw = read_fence()
        (output / 'fence-paused.txt').write_text(raw)
        vp = initial['video-params']
        fps = initial.get('container-fps')
        source_fps = f'{fps:.2f}' if number(fps) else 'n/a'
        ipc.call('show-text',
                 f'PS4 UVD | vaapi-copy | {vp["w"]}x{vp["h"]} | source {source_fps} fps\n'
                 f'Paused verification | drops VO {initial["frame-drop-count"]} / decoder {initial["decoder-frame-drop-count"]}\n'
                 f'UVD completed {paused_fence["completed"]} / emitted {paused_fence["emitted"]}', 2000, 0)
        time.sleep(.3)  # Warm the real font/overlay while the video is still paused.
        gate(ipc.snapshot(), initial=True)
        if not single_hwdec_thread((output / 'mpv.log').read_text(errors='replace')):
            raise RuntimeError('Missing actual single-thread initialization request')
        if time.monotonic() >= deadline:
            raise RuntimeError('Paused verification/OSD warmup exceeded 20 seconds')
        progress = Progress(initial['duration'], initial['time-pos'], paused_fence, time.monotonic())
        ipc.call('set_property', 'pause', False)  # Exactly one explicit unpause; no seeks/retries.
        log_positions = {name: (0, '') for name in ('mpv.log', 'stdout.txt', 'stderr.txt')}
        ready = False
        with (output / 'telemetry.jsonl').open('x', buffering=1) as telemetry:
            while not stopping['reason']:
                if child.poll() is not None:
                    raise RuntimeError('mpv exited unexpectedly: ' + str(child.returncode))
                for name, (offset, tail) in log_positions.items():
                    log = output / name
                    if log.exists():
                        with log.open(errors='replace') as f:
                            f.seek(offset); text = tail + f.read(); offset = f.tell()
                        match = TERMINAL.search(text)
                        if match:
                            raise RuntimeError('Terminal ' + name + ': ' + match.group(0))
                        log_positions[name] = (offset, text[-512:])
                s = ipc.snapshot()
                fence, raw = read_fence()
                now = time.monotonic()
                metrics = progress.update(s, fence, now)
                row = {'monotonic': now, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                       'player': s, 'uvd_fences': fence, **metrics}
                telemetry.write(json.dumps(row, sort_keys=True) + '\n')
                fmt = lambda x: f'{x:.2f}' if number(x) else 'n/a'
                vp = s['video-params']
                osd = (f'PS4 LIVERPOOL | UVD {s["hwdec-current"]} | {vp["w"]}x{vp["h"]}\n'
                       f'Source {fmt(s["container-fps"])} fps | H.264 | Mesa 26.2.5 | fallback disabled\n'
                       f'Playback speed {fmt(metrics["pts_wall_speed"])}x | pass {metrics["current_pass"]} | completed {progress.wraps}\n'
                       f'Dropped frames: display {s["frame-drop-count"]} / decoder {s["decoder-frame-drop-count"]}\n'
                       f'UVD completed {fence["completed"]} (+{metrics["fence_completed_delta"]}/sample) / emitted {fence["emitted"]}')
                ipc.call('show-text', osd, 1500, 0)
                if not ready and progress.wraps >= 3 and progress.clean:
                    save(output / 'READY.json', {'scope': 'three completed clean passes; subsequent running time remains unqualified', **row})
                    ready = True
                time.sleep(1)
        reason = stopping['reason']
    except Exception as exc:
        reason = str(exc)
        save(output / 'FAULT.json', {'reason': reason, 'no_retry': True})
    finally:
        if child is not None and child.poll() is None:
            try:
                if ipc:
                    ipc.call('quit')
                else:
                    child.terminate()
            except Exception:
                child.terminate()  # mpv SIGTERM requests its normal shutdown; never SIGKILL/reset.
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                reason += '; mpv did not quit within 5 seconds; PID retained for operator'
        if ipc:
            ipc.close()
        save(output / 'STOPPED.json', {'reason': reason, 'mpv_pid': child.pid if child else None,
             'mpv_exit': child.poll() if child else None, 'no_retry': True, 'driver_reset': False})
    return 1 if (output / 'FAULT.json').exists() else 0


if __name__ == '__main__':
    raise SystemExit(main())
