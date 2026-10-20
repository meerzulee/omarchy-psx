#!/usr/bin/env python3
"""Build the pinned PS4 Mesa candidate into an isolated, unprivileged stage."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import time


OPTIONS = [
    '--prefix=/usr', '--libdir=lib', '--buildtype=release',
    '-Db_ndebug=false', '-Db_lto=false', '-Dplatforms=x11,wayland',
    '-Dgallium-drivers=radeonsi', '-Dvulkan-drivers=amd', '-Dglx=dri',
    '-Degl=enabled', '-Dgbm=enabled', '-Dglvnd=enabled',
    '-Dgles1=disabled', '-Dgles2=enabled', '-Dllvm=disabled',
    '-Damd-use-llvm=false', '-Ddraw-use-llvm=false',
    '-Dgallium-va=enabled', '-Dvideo-codecs=h264dec',
    '-Dgallium-rusticl=false', '-Dmicrosoft-clc=disabled',
    '-Dbuild-tests=true', '-Dbuild-radv-tests=false',
    '-Dbuild-aco-tests=false', '-Dglx-read-only-text=true',
    '-Dtools=', '--wrap-mode=nofallback',
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--work', type=Path, required=True,
                    help='New output directory; existing paths are refused')
    ap.add_argument('--meson', type=Path, required=True)
    ap.add_argument('--jobs', type=int, default=6)
    ap.add_argument('--resume', action='store_true',
                    help='Resume an incomplete work directory after verifying all source pins')
    args = ap.parse_args()
    if sys.platform != 'linux' or platform.machine() != 'x86_64':
        ap.error('Build natively on Linux x86_64; this is not a Darwin builder')
    if not 1 <= args.jobs <= 64:
        ap.error('--jobs must be 1..64')
    here = Path(__file__).resolve().parent
    inputs = json.loads((here / 'sources.json').read_text())
    archive = args.archive.resolve(strict=True)
    if sha(archive) != inputs['upstream']['sha256']:
        ap.error('Official source archive SHA256 mismatch')
    patches = []
    for pin in inputs['patches']:
        p = here / pin['path']
        if sha(p) != pin['sha256']:
            ap.error(f'Patch SHA256 mismatch: {p.name}')
        patches.append(p)
    meson = args.meson.absolute()
    if not meson.is_file() or not os.access(meson, os.X_OK):
        ap.error('--meson must name an executable (for example in a venv)')
    work = args.work.absolute()
    if not args.resume:
        work.mkdir(parents=True, exist_ok=False)
    elif not work.is_dir() or (work / 'stage').exists() or (work / 'RESULT.json').exists():
        ap.error('--resume requires an incomplete directory with no staged candidate')
    source = work / ('mesa-' + inputs['upstream']['version'])
    build = work / 'build'
    stage = work / 'stage'
    env = dict(os.environ)
    env.update(PATH=str(meson.parent) + ':/usr/bin:/bin', CC='gcc', CXX='g++',
               CFLAGS='-march=x86-64 -mtune=generic',
               CXXFLAGS='-march=x86-64 -mtune=generic')
    # Ambient build/loader settings must not silently alter a candidate.
    for key in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CPPFLAGS', 'LDFLAGS',
                'PKG_CONFIG_PATH', 'PKG_CONFIG_LIBDIR', 'MESON_ARGS'):
        env.pop(key, None)
    commands = json.loads((work / 'COMMANDS.json').read_text()) if args.resume else []
    suffix = ''
    if args.resume:
        suffix = '-resume-' + str(len(list(work.glob('RESUME-*.json'))) + 1)

    def run(name: str, argv: list[str], cwd: Path | None = None) -> None:
        name += suffix
        log = work / (name + '.log')
        start = time.monotonic()
        print(name, flush=True)
        with log.open('xb') as out:
            proc = subprocess.run(argv, cwd=cwd, env=env,
                                  stdout=out, stderr=subprocess.STDOUT)
        commands.append(dict(phase=name, argv=argv, exit_code=proc.returncode,
                             log=log.name,
                             elapsed_seconds=time.monotonic() - start,
                             log_sha256=sha(log)))
        save(work / 'COMMANDS.json', commands)
        if proc.returncode:
            print(log.read_text(errors='replace')[-8000:], file=sys.stderr)
            raise RuntimeError(f'{name} failed; inspect {log}')

    input_receipt = dict(
        inputs=inputs, builder_sha256=sha(Path(__file__).resolve()),
        options=OPTIONS, architecture=platform.machine(),
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        environment={k: env[k] for k in ('PATH', 'CC', 'CXX', 'CFLAGS', 'CXXFLAGS')},
    )
    if args.resume:
        prior = json.loads((work / 'INPUTS.json').read_text())
        if any(prior[k] != input_receipt[k] for k in ('inputs', 'options', 'environment')):
            raise RuntimeError('Cannot resume different source/options/environment')
        for name, expected_sha in json.loads((work / 'SOURCE.json').read_text()).items():
            if sha(source / name) != expected_sha:
                raise RuntimeError(f'Cannot resume changed source: {name}')
        save(work / ('RESUME' + suffix.removeprefix('-resume') + '.json'), input_receipt)
    else:
        save(work / 'INPUTS.json', input_receipt)
        with tarfile.open(archive) as tf:
            members = tf.getmembers()
            prefix = source.name + '/'
            if any(m.name != source.name and not m.name.startswith(prefix) for m in members):
                raise RuntimeError('Archive has an unexpected top-level directory')
            tf.extractall(work, filter='data')
        if (source / 'VERSION').read_text().strip() != inputs['upstream']['version']:
            raise RuntimeError('Source VERSION mismatch')
        for i, patch in enumerate(patches, 1):
            run(f'patch-{i:02d}-check', ['git', 'apply', '--check', str(patch)], source)
            run(f'patch-{i:02d}', ['git', 'apply', str(patch)], source)
        source_files = {str(p.relative_to(source)): sha(p)
                        for p in sorted(source.rglob('*')) if p.is_file()}
        save(work / 'SOURCE.json', source_files)
    setup = ['--reconfigure'] if args.resume else []
    run('configure', [str(meson), 'setup', *setup, str(build), str(source), *OPTIONS])
    run('compile', [str(meson.parent / 'ninja'), '-C', str(build), '-j', str(args.jobs)])
    # Meson builds build_by_default:false test dependencies (glcpp/glsl_compiler).
    # A plain Ninja default build does not include those executables.
    run('tests', [str(meson), 'test', '-C', str(build),
                  '--print-errorlogs', '--num-processes', str(args.jobs)])
    run('stage', [str(meson), 'install', '-C', str(build), '--no-rebuild',
                  '--destdir', str(stage)])
    notices = stage / 'usr/share/doc/mesa-psx-candidate'
    notices.mkdir(parents=True)
    shutil.copy2(source / 'docs/license.rst', notices / 'upstream-license.rst')
    shutil.copytree(source / 'licenses', notices / 'licenses')
    shutil.copy2(here / 'sources.json', notices / 'sources.json')
    for p in patches:
        shutil.copy2(p, notices / p.name)
    files = {}
    for p in sorted(stage.rglob('*')):
        if p.is_symlink():
            p.resolve().relative_to(stage.resolve())
            files[str(p.relative_to(stage))] = {'symlink': os.readlink(p)}
        elif p.is_file():
            files[str(p.relative_to(stage))] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    for required in ('usr/lib/libEGL_mesa.so.0', 'usr/lib/libGLX_mesa.so.0',
                     'usr/lib/dri/radeonsi_dri.so', 'usr/lib/dri/radeonsi_drv_video.so',
                     'usr/lib/libvulkan_radeon.so', 'usr/lib/libgbm.so.1',
                     'usr/lib/gbm/dri_gbm.so'):
        if required not in files:
            raise RuntimeError(f'Missing staged driver: {required}')
    receipt = dict(schema=1, status='BUILT_TESTED_STAGED_NOT_HARDWARE_QUALIFIED',
                   mesa_version=inputs['upstream']['version'], inputs=inputs,
                   source_manifest_sha256=sha(work / 'SOURCE.json'),
                   commands_sha256=sha(work / 'COMMANDS.json'), files=files,
                   hardware_acceptance=False, system_installation=False)
    save(stage / 'MESA-PSX-CANDIDATE.json', receipt)
    with tarfile.open(work / 'mesa-psx-candidate.tar.xz', 'x:xz') as tf:
        tf.add(stage, arcname='mesa-psx-candidate')
    save(work / 'RESULT.json', dict(
        status=receipt['status'], hardware_acceptance=False,
        archive_sha256=sha(work / 'mesa-psx-candidate.tar.xz'),
        archive_bytes=(work / 'mesa-psx-candidate.tar.xz').stat().st_size,
        stage_manifest_sha256=sha(stage / 'MESA-PSX-CANDIDATE.json'),
        source_manifest_sha256=sha(work / 'SOURCE.json'),
    ))
    print(work / 'RESULT.json', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
