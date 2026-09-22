#!/usr/bin/env python3
"""Convert a short video excerpt into a size-bounded animated GIF for WeChat articles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


class ConversionError(RuntimeError):
    pass


def render_attempt(
    source: Path,
    output: Path,
    *,
    start: float,
    duration: float,
    width: int,
    fps: int,
    colors: int,
) -> None:
    video_filter = (
        f"fps={fps},scale={width}:-2:flags=lanczos:force_original_aspect_ratio=decrease,"
        "split[v0][v1];"
        f"[v0]palettegen=max_colors={colors}:stats_mode=diff[p];"
        "[v1][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle"
    )
    process = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-i",
            str(source),
            "-filter_complex",
            video_filter,
            "-loop",
            "0",
            "-y",
            str(output),
        ],
        text=True,
        capture_output=True,
    )
    if process.returncode != 0:
        raise ConversionError(process.stderr.strip() or "ffmpeg conversion failed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start", type=float, default=0.0, help="Excerpt start time in seconds")
    parser.add_argument("--duration", type=float, default=6.0, help="Excerpt duration in seconds")
    parser.add_argument("--width", type=int, default=720, help="Maximum GIF width")
    parser.add_argument("--fps", type=int, default=10, help="Initial GIF frame rate")
    parser.add_argument("--colors", type=int, default=128, help="Initial palette size")
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=5_000_000,
        help="Hard output-size limit; conversion fails if no candidate fits",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source = args.input.resolve()
    output = args.output.resolve()
    try:
        if not shutil.which("ffmpeg"):
            raise ConversionError("ffmpeg is not installed or not on PATH")
        if not source.is_file():
            raise ConversionError(f"input video not found: {source}")
        if output.suffix.lower() != ".gif":
            raise ConversionError("output must use the .gif extension")
        if args.start < 0 or not 0.5 <= args.duration <= 15:
            raise ConversionError("start must be >= 0 and duration must be between 0.5 and 15 seconds")
        if args.width < 240 or args.fps < 4 or not 32 <= args.colors <= 256:
            raise ConversionError("width must be >= 240, fps >= 4, and colors between 32 and 256")
        if args.max_bytes < 100_000:
            raise ConversionError("max-bytes must be at least 100000")

        output.parent.mkdir(parents=True, exist_ok=True)
        attempts: list[dict[str, int]] = []
        profiles = [
            (args.width, args.fps, args.colors),
            (args.width, max(6, args.fps - 2), min(args.colors, 96)),
            (max(480, int(args.width * 0.85)), max(6, args.fps - 2), 80),
            (max(420, int(args.width * 0.75)), 6, 64),
            (max(360, int(args.width * 0.65)), 5, 48),
        ]
        seen: set[tuple[int, int, int]] = set()
        with tempfile.TemporaryDirectory(prefix="wechat-gif-") as tmp:
            for index, (width, fps, colors) in enumerate(profiles, start=1):
                profile = (width, fps, colors)
                if profile in seen:
                    continue
                seen.add(profile)
                candidate = Path(tmp) / f"attempt-{index}.gif"
                render_attempt(
                    source,
                    candidate,
                    start=args.start,
                    duration=args.duration,
                    width=width,
                    fps=fps,
                    colors=colors,
                )
                size = candidate.stat().st_size
                attempts.append({"width": width, "fps": fps, "colors": colors, "bytes": size})
                if size <= args.max_bytes:
                    shutil.copyfile(candidate, output)
                    print(
                        json.dumps(
                            {
                                "success": True,
                                "output": str(output),
                                "bytes": size,
                                "start": args.start,
                                "duration": args.duration,
                                "width": width,
                                "fps": fps,
                                "colors": colors,
                                "attempts": attempts,
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 0

        raise ConversionError(
            f"no GIF candidate fit within {args.max_bytes} bytes; shorten duration or lower width/fps"
        )
    except ConversionError as error:
        print(json.dumps({"success": False, "error": str(error)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
