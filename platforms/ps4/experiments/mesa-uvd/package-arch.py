#!/usr/bin/env python3
"""Package the exact verified Mesa stage; never install or resolve packages."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--archive', type=Path, required=True)
ap.add_argument('--archive-sha256', required=True)
ap.add_argument('--manifest-sha256', required=True)
ap.add_argument('--mesa-source', type=Path, required=True)
ap.add_argument('--candidate', required=True, help='Exact sources.json candidate identity')
ap.add_argument('--pkgrel', required=True, help='Distinct Arch release for this candidate')
ap.add_argument('--output', type=Path, required=True)
args = ap.parse_args()
for pin in (args.archive_sha256, args.manifest_sha256):
    if not re.fullmatch(r'[0-9a-f]{64}', pin):
        ap.error('Expected a lowercase SHA256 pin')
if not re.fullmatch(r'[1-9][0-9]*(?:\.[0-9]+)?', args.pkgrel):
    ap.error('Expected a numeric Arch pkgrel')
archive = args.archive.resolve(strict=True)
source = args.mesa_source.resolve(strict=True)
assert hashlib.sha256(archive.read_bytes()).hexdigest() == args.archive_sha256
pins = json.loads((source / 'sources.json').read_text())
if pins['candidate'] != args.candidate:
    ap.error('Candidate differs from the explicitly selected identity')
version = pins['upstream']['version']
if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
    ap.error('Expected a numeric Mesa version')
out = args.output.absolute()
out.mkdir(parents=True, exist_ok=False)
shutil.copy2(archive, out / 'candidate.tar.xz')
for name in ('with-mesa.py', 'sources.json'):
    shutil.copy2(source / name, out / name)
checksums = [hashlib.sha256((out / n).read_bytes()).hexdigest()
             for n in ('candidate.tar.xz', 'with-mesa.py', 'sources.json')]
recipe = r'''# Locally rebuilt exact tested stage; no upstream repository resolution.
pkgbase=mesa-psx
pkgname=(mesa vulkan-radeon)
epoch=1
pkgver=MESA_VERSION
pkgrel=PACKAGE_RELEASE
arch=(x86_64)
url='https://github.com/meerzulee/linux-psx/tree/master/userspace/mesa'
license=(MIT BSD-3-Clause SGI-B-2.0)
options=(!strip !debug !lto)
source=(candidate.tar.xz with-mesa.py sources.json)
sha256sums=(CHECKSUMS)
prepare() {
  /usr/bin/python3 "$srcdir/with-mesa.py" --root "$srcdir/mesa-psx-candidate" \
    --expected-manifest-sha256 MANIFEST --verify-only
}
package_mesa() {
  pkgdesc='Experimental PS4 Liverpool Mesa from the pinned psX candidate'
  depends=(expat glibc libdrm libelf libgcc libglvnd libstdc++ libx11 libxcb
           libxext libxshmfence libxxf86vm lm_sensors spirv-tools wayland zlib zstd)
  provides=("libva-mesa-driver=$epoch:$pkgver-$pkgrel" "mesa-libgl=$epoch:$pkgver-$pkgrel"
            libva-driver opengl-driver)
  conflicts=('libva-mesa-driver<1:24.2.7-1' 'mesa-libgl<17.0.1-2')
  cp -a "$srcdir/mesa-psx-candidate/usr" "$pkgdir/usr"
  rm "$pkgdir/usr/lib/libvulkan_radeon.so"
  rm "$pkgdir/usr/share/vulkan/icd.d/radeon_icd.x86_64.json"
  rm "$pkgdir/usr/share/drirc.d/00-radv-defaults.conf"
  rmdir "$pkgdir/usr/share/vulkan/icd.d" "$pkgdir/usr/share/vulkan"
  ln -s libGLX_mesa.so.0 "$pkgdir/usr/lib/libGLX_indirect.so.0"
  install -Dm644 "$srcdir/mesa-psx-candidate/usr/share/doc/mesa-psx-candidate/upstream-license.rst" \
    "$pkgdir/usr/share/licenses/mesa/license.rst"
}
package_vulkan-radeon() {
  pkgdesc='PS4 Liverpool RADV from the matching Mesa candidate'
  depends=("mesa=$epoch:$pkgver-$pkgrel" expat glibc libdisplay-info libdrm
           libelf libgcc libstdc++ libx11 libxcb libxshmfence spirv-tools
           systemd-libs vulkan-icd-loader vulkan-mesa-implicit-layers
           wayland xcb-util-keysyms zlib zstd)
  provides=(vulkan-driver)
  for path in usr/lib/libvulkan_radeon.so usr/share/vulkan/icd.d/radeon_icd.x86_64.json \
              usr/share/drirc.d/00-radv-defaults.conf; do
    install -Dm644 "$srcdir/mesa-psx-candidate/$path" "$pkgdir/$path"
  done
  install -Dm644 "$srcdir/mesa-psx-candidate/usr/share/doc/mesa-psx-candidate/upstream-license.rst" \
    "$pkgdir/usr/share/licenses/vulkan-radeon/license.rst"
}
'''
recipe = recipe.replace('CHECKSUMS', ' '.join("'" + s + "'" for s in checksums))
recipe = recipe.replace('MANIFEST', args.manifest_sha256)
recipe = recipe.replace('MESA_VERSION', version).replace('PACKAGE_RELEASE', args.pkgrel)
(out / 'PKGBUILD').write_text(recipe)
# Only a local data-only package build. No -s, pacman, install script or service.
subprocess.run(['/usr/bin/makepkg', '--nodeps', '--noconfirm'], cwd=out,
               env=dict(os.environ, PATH='/usr/bin:/bin', LC_ALL='C'), check=True)
packages = sorted(out.glob('*.pkg.tar.*'))
assert len(packages) == 2
result = {'source_candidate': pins['candidate'], 'candidate_archive_sha256': args.archive_sha256,
          'candidate_manifest_sha256': args.manifest_sha256,
          'package_version': f'1:{version}-{args.pkgrel}',
          'packaging_inputs': {n: hashlib.sha256((out / n).read_bytes()).hexdigest()
                               for n in ('PKGBUILD', 'with-mesa.py', 'sources.json')},
          'packages': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in packages},
          'installation': False, 'hardware_acceptance': False}
(out / 'PACKAGES.json').write_text(json.dumps(result, indent=2) + '\n')
artifacts = packages + [out / n for n in ('candidate.tar.xz', 'PKGBUILD', 'with-mesa.py',
                                        'sources.json', 'PACKAGES.json')]
(out / 'SHA256SUMS').write_text(''.join(
    f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n'
    for p in sorted(artifacts, key=lambda p: p.name)))
print(json.dumps(result))
