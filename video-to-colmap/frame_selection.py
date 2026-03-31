#!/usr/bin/env python3
"""
frame_selection.py
Extracts sharp frames from a video using the sharp-frames CLI.
Requires: pip install sharp-frames, FFmpeg on PATH
"""

import subprocess
from pathlib import Path


def build_command(
    input_path: str,
    output_path: str,
    fps: int = 10,
    fmt: str = "jpg",
    width: int = 0,
    selection_method: str = "batched",
    # best-n
    num_frames: int = 300,
    min_buffer: int = 3,
    # batched
    batch_size: int = 5,
    batch_buffer: int = 2,
    # outlier-removal
    outlier_window: int = 15,
    outlier_sensitivity: int = 60,
) -> list[str]:
    cmd = [
        "sharp-frames", input_path, output_path,
        "--fps", str(fps),
        "--format", fmt,
        "--selection-method", selection_method,
        "--force-overwrite",
    ]

    if width > 0:
        cmd += ["--width", str(width)]

    if selection_method == "best-n":
        cmd += [
            "--num-frames", str(num_frames),
            "--min-buffer", str(min_buffer),
        ]
    elif selection_method == "batched":
        cmd += [
            "--batch-size", str(batch_size),
            "--batch-buffer", str(batch_buffer),
        ]
    elif selection_method == "outlier-removal":
        cmd += [
            "--outlier-window-size", str(outlier_window),
            "--outlier-sensitivity", str(outlier_sensitivity),
        ]

    return cmd


def run_frame_selection(
    input_video: str,
    output_dir: str,
    fps: int = 10,
    fmt: str = "jpg",
    width: int = 0,
    selection_method: str = "batched",
    num_frames: int = 300,
    min_buffer: int = 3,
    batch_size: int = 5,
    batch_buffer: int = 2,
    outlier_window: int = 15,
    outlier_sensitivity: int = 60,
) -> int:
    """
    Run sharp-frames and return the number of extracted frames.
    Raises subprocess.CalledProcessError on failure.
    """
    input_path = Path(input_video)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    output_path.mkdir(parents=True, exist_ok=True)

    cmd = build_command(
        str(input_path), str(output_path),
        fps=fps, fmt=fmt, width=width,
        selection_method=selection_method,
        num_frames=num_frames, min_buffer=min_buffer,
        batch_size=batch_size, batch_buffer=batch_buffer,
        outlier_window=outlier_window, outlier_sensitivity=outlier_sensitivity,
    )

    subprocess.run(cmd, check=True)

    frames = list(output_path.glob(f"*.{fmt}"))
    return len(frames)