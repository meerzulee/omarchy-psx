#!/usr/bin/env python3
"""Read-only checks for explicit 720p30/1080p30 I/P fractal fixtures; no hardware API."""
import argparse
import collections
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess

FPS, FRAMES = 30, 900
VARIANTS = {
    "720p30": {"width": 1280, "height": 720, "level": 31,
               "render_width": 1920, "render_height": 1080, "maxrate": "10M", "bufsize": "10M"},
    "1080p30": {"width": 1920, "height": 1080, "level": 41,
                "render_width": 2880, "render_height": 1620, "maxrate": "20M", "bufsize": "40M"},
}


def frame_bytes(variant="720p30"):
    spec = VARIANTS[variant]
    return spec["width"] * spec["height"] * 3 // 2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mp4_boxes(path):
    boxes = []
    with Path(path).open("rb") as handle:
        length = Path(path).stat().st_size
        while handle.tell() < length:
            offset = handle.tell()
            header = handle.read(8)
            require(len(header) == 8, "Truncated MP4 box header")
            size, kind = struct.unpack(">I4s", header)
            if size == 1:
                extended = handle.read(8)
                require(len(extended) == 8, "Truncated extended MP4 box")
                size = struct.unpack(">Q", extended)[0]
                minimum = 16
            else:
                minimum = 8
            if size == 0:
                size = length - offset
            require(size >= minimum and offset + size <= length, "Invalid MP4 box size")
            boxes.append({"type": kind.decode("ascii", "replace"), "offset": offset, "bytes": size})
            handle.seek(offset + size)
    return boxes


def probe(path, ffprobe, ffmpeg=None):
    common = [str(ffprobe), "-v", "error", "-select_streams", "v:0"]
    commands = {
        "streams": common + ["-show_streams", "-show_format", "-of", "json", str(path)],
        "packets": common + ["-show_packets", "-show_entries", "packet=pts,dts,duration,flags", "-of", "json", str(path)],
        "frames": common + ["-show_frames", "-show_entries", "frame=pict_type,key_frame,best_effort_timestamp", "-of", "json", str(path)]}
    result = {name: json.loads(subprocess.check_output(argv)) for name, argv in commands.items()}
    ffmpeg = ffmpeg or shutil.which("ffmpeg")
    require(ffmpeg is not None, "ffmpeg with trace_headers is required")
    headers = [str(ffmpeg), "-nostdin", "-hide_banner", "-v", "info", "-i", str(path),
               "-map", "0:v:0", "-c:v", "copy", "-bsf:v", "trace_headers", "-frames:v", "1", "-f", "null", "-"]
    trace = subprocess.run(headers, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=True)
    result["header_trace"] = {"argv": headers, "stderr": trace.stderr, "returncode": trace.returncode}
    result["probe_commands"] = commands
    return result


def validate_probe(data, path, variant="720p30"):
    spec = VARIANTS[variant]
    width, height, level = spec["width"], spec["height"], spec["level"]
    streams = data["streams"]["streams"]
    require(data["streams"]["format"]["nb_streams"] == 1, "Exactly one container stream required")
    require(len(streams) == 1, "Exactly one selected video stream required")
    stream = streams[0]
    for key, value in {
        "codec_name": "h264", "profile": "Constrained Baseline", "level": level,
        "width": width, "height": height, "pix_fmt": "yuv420p", "has_b_frames": 0,
        "bits_per_raw_sample": "8",
        "field_order": "progressive", "color_range": "tv", "color_space": "bt709",
        "color_transfer": "bt709", "color_primaries": "bt709",
    }.items():
        require(stream.get(key) == value, f"Unexpected {key}: {stream.get(key)!r}")
    header_fields = {"profile_idc": 66, "constraint_set0_flag": 1, "constraint_set1_flag": 1,
                     "level_idc": level, "max_num_ref_frames": 1, "entropy_coding_mode_flag": 0,
                     "num_ref_idx_l0_default_active_minus1": 0, "video_full_range_flag": 0,
                     "colour_primaries": 1, "transfer_characteristics": 1, "matrix_coefficients": 1}
    coded_width = (width + 15) // 16 * 16
    coded_height = (height + 15) // 16 * 16
    header_fields.update(pic_width_in_mbs_minus1=coded_width // 16 - 1,
                         pic_height_in_map_units_minus1=coded_height // 16 - 1,
                         frame_mbs_only_flag=1,
                         frame_cropping_flag=int(coded_height != height or coded_width != width))
    if header_fields["frame_cropping_flag"]:
        header_fields.update(frame_crop_left_offset=0, frame_crop_top_offset=0,
                             frame_crop_right_offset=(coded_width - width) // 2,
                             frame_crop_bottom_offset=(coded_height - height) // 2)
    for field, value in header_fields.items():
        values = re.findall(rf"\b{re.escape(field)}\s+[01]+\s*=\s*(\d+)\s*$",
                            data["header_trace"]["stderr"], re.MULTILINE)
        require(values and set(map(int, values)) == {value}, f"Unexpected H.264 header field {field}")
    require(Fraction(stream["avg_frame_rate"]) == FPS, "Wrong average frame rate")
    require(Fraction(stream["r_frame_rate"]) == FPS, "Wrong nominal frame rate")
    require(int(stream["nb_frames"]) == FRAMES, "Wrong container frame count")
    timebase = Fraction(stream["time_base"])
    packets = data["packets"]["packets"]
    frames = data["frames"]["frames"]
    require(len(packets) == len(frames) == FRAMES, "Wrong parsed packet/frame count")
    for index, (packet, frame) in enumerate(zip(packets, frames)):
        expected = Fraction(index, FPS)
        require(Fraction(packet["pts"]) * timebase == expected, "Nonuniform packet PTS")
        require(Fraction(packet["dts"]) * timebase == expected, "Unexpected reorder or DTS")
        require(Fraction(packet["duration"]) * timebase == Fraction(1, FPS), "Wrong sample duration")
        require(Fraction(frame["best_effort_timestamp"]) * timebase == expected, "Wrong decoded timestamp")
        require(frame["pict_type"] in ("I", "P"), "Non-I/P picture")
        require(frame["pict_type"] == ("I" if index % 60 == 0 else "P"), "Unexpected fixed GOP")
    counts = dict(collections.Counter(frame["pict_type"] for frame in frames))
    require(counts == {"I": 15, "P": 885}, "Wrong I/P distribution")
    require(Fraction(data["streams"]["format"]["duration"]) == 30, "Wrong MP4 duration")
    boxes = mp4_boxes(path)
    kinds = [box["type"] for box in boxes]
    require(kinds.count("moov") == kinds.count("mdat") == 1, "Unexpected MP4 structure")
    require(kinds.index("moov") < kinds.index("mdat"), "MP4 is not faststart")
    return {"status": "PASS_MEDIA_STRUCTURE", "variant": variant, "width": width, "height": height,
            "coded_width": coded_width, "coded_height": coded_height,
            "fps": FPS, "frames": FRAMES, "duration_seconds": 30,
            "profile": stream["profile"], "level": stream["level"],
            "pixel_format": stream["pix_fmt"], "picture_types": counts,
            "header_fields": header_fields,
            "uniform_pts_and_dts": True, "faststart": True, "mp4_boxes": boxes}


def frame_md5(text, variant="720p30"):
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        row = [part.strip() for part in line.split(",")]
        require(len(row) == 6, "Malformed framemd5 line")
        require(all(character in "0123456789abcdef" for character in row[5]) and len(row[5]) == 32,
                "Malformed frame MD5")
        rows.append([*[int(item) for item in row[:5]], row[5]])
    require(len(rows) == FRAMES, "Wrong reference frame count")
    for index, row in enumerate(rows):
        require(row[:5] == [0, index, index, 1, frame_bytes(variant)], "Wrong reference layout/timestamps")
    require(len({row[5] for row in rows}) == FRAMES, "Duplicate decoded frames")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--variant", choices=VARIANTS, default="720p30")
    parser.add_argument("--framemd5", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--decode", action="store_true", help="Software-decode and compare the pinned framemd5; no writes")
    args = parser.parse_args()
    ffprobe = shutil.which("ffprobe")
    require(ffprobe is not None, "ffprobe is required")
    identity = sha256(args.video)
    if args.expected_sha256:
        require(identity == args.expected_sha256, "Video SHA256 mismatch")
    result = validate_probe(probe(args.video, ffprobe), args.video, args.variant)
    result["sha256"] = identity
    if args.framemd5:
        expected = frame_md5(args.framemd5.read_text(), args.variant)
        result["unique_reference_frames"] = len(expected)
        result["reference_framemd5_sha256"] = sha256(args.framemd5)
    if args.decode:
        require(args.framemd5 is not None, "--decode requires --framemd5")
        ffmpeg = shutil.which("ffmpeg")
        require(ffmpeg is not None, "ffmpeg is required")
        argv = [ffmpeg, "-nostdin", "-v", "error", "-hwaccel", "none", "-c:v", "h264",
                "-i", str(args.video), "-map", "0:v:0", "-an", "-sn", "-dn", "-pix_fmt", "nv12",
                "-c:v", "rawvideo", "-f", "framemd5", "-"]
        actual = frame_md5(subprocess.check_output(argv, text=True), args.variant)
        require(actual == expected, "Software decoded frames differ from reference")
        result["software_reference_match"] = True
        result["decode_argv"] = argv
    result["hardware_acceptance"] = False
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
