#!/usr/bin/env python3
"""Verify and select an isolated Mesa stage for one explicitly supplied command."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


def verify(root: Path) -> dict:
    root = root.resolve(strict=True)
    manifest = json.loads((root / 'MESA-PSX-CANDIDATE.json').read_text())
    expected = json.loads(Path(__file__).with_name('sources.json').read_text())
    if (manifest.get('schema') != 1 or manifest.get('hardware_acceptance') is not False
            or manifest.get('status') != 'BUILT_TESTED_STAGED_NOT_HARDWARE_QUALIFIED'
            or manifest.get('mesa_version') != expected['upstream']['version']
            or manifest.get('inputs') != expected):
        raise ValueError('Not an experimental Mesa candidate manifest')
    files = manifest['files']
    required = {
        'usr/lib/libEGL_mesa.so.0', 'usr/lib/libGLX_mesa.so.0',
        'usr/lib/libgbm.so.1', 'usr/lib/dri/radeonsi_dri.so',
        'usr/lib/dri/radeonsi_drv_video.so', 'usr/lib/libvulkan_radeon.so',
        'usr/lib/gbm/dri_gbm.so',
    }
    icds = [n for n in files if n.startswith('usr/share/vulkan/icd.d/radeon_icd')
            and n.endswith('.json')]
    if not required.issubset(files) or len(icds) != 1:
        raise ValueError('Incomplete driver/ICD manifest')
    actual = {str(p.relative_to(root)) for p in (root / 'usr').rglob('*')
              if p.is_file() or p.is_symlink()}
    if actual != set(files):
        raise ValueError('Staged files differ from manifest (missing or unlisted files)')
    for name, pin in manifest['files'].items():
        if not name.startswith('usr/') or '..' in Path(name).parts:
            raise ValueError(f'Invalid manifest path: {name}')
        p = root / name
        if p.is_symlink():
            if set(pin) != {'symlink'} or os.readlink(p) != pin['symlink']:
                raise ValueError(f'Symlink mismatch: {name}')
            p.resolve(strict=True).relative_to(root)
        else:
            p.resolve(strict=True).relative_to(root)
            if (not stat.S_ISREG(p.lstat().st_mode) or set(pin) != {'sha256', 'bytes'}
                    or p.stat().st_size != pin['bytes']
                    or hashlib.sha256(p.read_bytes()).hexdigest() != pin['sha256']):
                raise ValueError(f'File hash mismatch: {name}')
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--expected-manifest-sha256',
                    help='Bind verification to the separately recorded build RESULT.json')
    ap.add_argument('--verify-only', action='store_true')
    ap.add_argument('--print-env', action='store_true')
    ap.add_argument('command', nargs=argparse.REMAINDER)
    args = ap.parse_args()
    root = args.root.resolve(strict=True)
    if root in (Path('/'), Path('/usr'), Path('/usr/local')):
        ap.error('Select an isolated candidate directory')
    if args.expected_manifest_sha256:
        actual = hashlib.sha256((root / 'MESA-PSX-CANDIDATE.json').read_bytes()).hexdigest()
        if actual != args.expected_manifest_sha256:
            ap.error('Candidate manifest differs from the expected build receipt')
    manifest = verify(root)
    if args.verify_only:
        print(json.dumps({'verified': True, 'mesa': manifest['mesa_version'],
                          'files': len(manifest['files']), 'hardware_acceptance': False}))
        return 0
    runtime = root / 'selection'
    runtime.mkdir(mode=0o700, exist_ok=True)
    egl = runtime / 'egl.json'
    egl.write_text(json.dumps({'file_format_version': '1.0.0',
                              'ICD': {'library_path': str(root / 'usr/lib/libEGL_mesa.so.0')}}) + '\n')
    vk = runtime / 'vulkan.json'
    manifests = list((root / 'usr/share/vulkan/icd.d').glob('radeon_icd*.json'))
    if len(manifests) != 1:
        raise ValueError('Expected exactly one Radeon Vulkan ICD manifest')
    vk_data = json.loads(manifests[0].read_text())
    vk_data['ICD']['library_path'] = str(root / 'usr/lib/libvulkan_radeon.so')
    vk.write_text(json.dumps(vk_data) + '\n')
    selection = {
        'LD_LIBRARY_PATH': str(root / 'usr/lib'),
        'LIBGL_DRIVERS_PATH': str(root / 'usr/lib/dri'),
        'LIBVA_DRIVERS_PATH': str(root / 'usr/lib/dri'),
        'LIBVA_DRIVER_NAME': 'radeonsi',
        'GBM_BACKENDS_PATH': str(root / 'usr/lib/gbm'),
        'GBM_BACKEND': 'dri',
        'MESA_LOADER_DRIVER_OVERRIDE': 'radeonsi',
        '__EGL_VENDOR_LIBRARY_FILENAMES': str(egl),
        '__GLX_VENDOR_LIBRARY_NAME': 'mesa',
        'VK_DRIVER_FILES': str(vk),
        'MESA_SHADER_CACHE_DIR': str(runtime / 'shader-cache'),
    }
    if args.print_env:
        print(json.dumps(selection, indent=2, sort_keys=True))
        return 0
    command = args.command
    if command[:1] == ['--']:
        command = command[1:]
    if not command:
        ap.error('Supply a command after --, or use --verify-only/--print-env')
    prefixes = ('LD_', 'MESA_', 'RADEON_', 'R600_', 'RADV_', 'AMD_',
                'LIBGL_', 'LIBVA_', 'GALLIUM_', 'EGL_', '__EGL_', '__GLX_',
                '__GL_', 'GBM_', 'VK_', 'ACO_', 'NIR_', 'GLSL_', 'SPIRV_')
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(prefixes) and k not in ('DRI_PRIME', 'DRI_PRIME_DEBUG')}
    env.update(selection)
    os.execvpe(command[0], command, env)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
