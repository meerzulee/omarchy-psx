#!/usr/bin/env python3
"""Validate the flashable USB MBR and extend only its second partition.

Imported historical partitioned media stay on schema 1. The image builder
authorizes this operation explicitly in a schema-2 image-layout record.
"""
import argparse
import array
import fcntl
import json
import os
from pathlib import Path
import stat
import struct
import subprocess

SECTOR = 512
BOOT_START = 2048
BOOT_SECTORS = 8388608
ROOT_START = BOOT_START + BOOT_SECTORS
ROOT_SIZE_OFFSET = 446 + 16 + 12
MINIMUM_DEVICE_BYTES = 32_000_000_000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def expanded_mbr(original, disk_sectors, base_image_bytes):
    """Return an MBR differing only in partition 2's length; never move data."""
    require(len(original) == SECTOR and original[510:] == b'\x55\xaa', 'invalid MBR signature')
    require(type(disk_sectors) is int and ROOT_START < disk_sectors <= 0xFFFFFFFF,
            'disk is outside the supported DOS/MBR size range')
    require(base_image_bytes % SECTOR == 0 and ROOT_START * SECTOR < base_image_bytes <= disk_sectors * SECTOR,
            'base image does not fit the USB')
    entries = [original[446 + i * 16:462 + i * 16] for i in range(4)]
    require(entries[2] == bytes(16) and entries[3] == bytes(16), 'expected exactly two primary partitions')
    boot, root = entries[:2]
    require(boot[0] == 0x80 and boot[4] == 0x0C and struct.unpack_from('<II', boot, 8) == (BOOT_START, BOOT_SECTORS),
            'boot partition must be active 4 GiB FAT32 at 1 MiB')
    start, length = struct.unpack_from('<II', root, 8)
    require(root[0] == 0 and root[4] == 0x83 and start == ROOT_START,
            'system partition must be inactive Linux partition 2 at the recorded offset')
    base_length = base_image_bytes // SECTOR - ROOT_START
    grown_length = disk_sectors - ROOT_START
    require(length in (base_length, grown_length), 'system partition has unexpected geometry')
    result = bytearray(original)
    struct.pack_into('<I', result, ROOT_SIZE_OFFSET, grown_length)
    return bytes(result)


def grow(disk, root, base_image_bytes, backup):
    require(os.geteuid() == 0, 'root privileges are required')
    disk, root = Path(disk).resolve(strict=True), Path(root).resolve(strict=True)
    require(disk.parent == Path('/dev') and root.parent == Path('/dev'), 'expected canonical block-device paths')
    disk_stat, root_stat = disk.stat(), root.stat()
    require(stat.S_ISBLK(disk_stat.st_mode) and stat.S_ISBLK(root_stat.st_mode), 'both targets must be block devices')
    root_sysfs = (Path('/sys/class/block') / root.name).resolve(strict=True)
    parent = root_sysfs.parent
    require('/usb' in str(root_sysfs) and parent.name == disk.name, 'root must belong to this USB disk')
    require((root_sysfs / 'partition').read_text().strip() == '2', 'running root must be partition 2')
    expected_device = f'{os.major(root_stat.st_rdev)}:{os.minor(root_stat.st_rdev)}'
    mounted_device = subprocess.check_output(['findmnt', '-nro', 'MAJ:MIN', '--target', '/'], text=True).strip()
    require(mounted_device == expected_device, 'target is not the running root filesystem')
    require((parent / 'dev').read_text().strip() == f'{os.major(disk_stat.st_rdev)}:{os.minor(disk_stat.st_rdev)}',
            'USB device identity changed')
    with disk.open('r+b', buffering=0) as device:
        require(os.fstat(device.fileno()).st_rdev == disk_stat.st_rdev, 'opened disk identity changed')
        size, sector_size = array.array('Q', [0]), array.array('I', [0])
        fcntl.ioctl(device.fileno(), 0x80081272, size, True)  # BLKGETSIZE64
        fcntl.ioctl(device.fileno(), 0x1268, sector_size, True)  # BLKSSZGET
        require(sector_size[0] == SECTOR and size[0] >= MINIMUM_DEVICE_BYTES, 'expected a 32 GB or larger, 512-sector USB')
        original = device.read(SECTOR)
        enlarged = expanded_mbr(original, size[0] // SECTOR, base_image_bytes)
        backup = Path(backup)
        require(backup.parent.is_dir() and not backup.is_symlink(), 'invalid MBR backup path')
        if original != enlarged:
            if backup.exists():
                require(backup.read_bytes() == original, 'existing MBR backup differs; inspect before retrying')
            else:
                descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, 'wb') as output:
                    output.write(original)
                    output.flush()
                    os.fsync(output.fileno())
                directory = os.open(backup.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            require(os.pwrite(device.fileno(), enlarged, 0) == SECTOR, 'short MBR write')
            os.fsync(device.fileno())
            require(os.pread(device.fileno(), SECTOR, 0) == enlarged, 'MBR read-back differs')
        # Repeat even if an earlier boot updated the MBR but stopped before the
        # kernel accepted the new length. The partition start never changes.
        subprocess.run(['partx', '--update', '--nr', '2', str(disk)], check=True)
        require(int((root_sysfs / 'size').read_text()) == size[0] // SECTOR - ROOT_START,
                'kernel did not accept the enlarged system partition')
    print(json.dumps({'partition': 2, 'start_sector': ROOT_START, 'disk_bytes': size[0]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disk', required=True)
    parser.add_argument('--root', required=True)
    parser.add_argument('--base-image-bytes', required=True, type=int)
    parser.add_argument('--backup', required=True)
    args = parser.parse_args()
    try:
        grow(args.disk, args.root, args.base_image_bytes, args.backup)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f'omarchy-ps4-partitioned-image: {error}\n')


if __name__ == '__main__':
    main()
