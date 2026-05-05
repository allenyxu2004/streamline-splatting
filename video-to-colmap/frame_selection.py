#!/usr/bin/env python3
"""
frame_selection.py
Extracts sharp frames from a video using the sharp-frames Python API.
"""

import sys
from pathlib import Path
from sharp_frames.sharp_frames import main as sharp_frames_main


def run_frame_selection(
    input_video: str,
    output_dir: str,
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
) -> int:
    """
    Run sharp-frames by calling its entry point directly.
    Returns the number of extracted frames.
    """
    input_path = Path(input_video)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    output_path.mkdir(parents=True, exist_ok=True)

    # Build the same argv that the CLI would receive
    args = [
        "sharp-frames",  # argv[0] program name
        str(input_path), str(output_path),
        "--fps", str(fps),
        "--format", fmt,
        "--selection-method", selection_method,
        "--force-overwrite",
    ]

    if width > 0:
        args += ["--width", str(width)]

    if selection_method == "best-n":
        args += [
            "--num-frames", str(num_frames),
            "--min-buffer", str(min_buffer),
        ]
    elif selection_method == "batched":
        args += [
            "--batch-size", str(batch_size),
            "--batch-buffer", str(batch_buffer),
        ]
    elif selection_method == "outlier-removal":
        args += [
            "--outlier-window-size", str(outlier_window),
            "--outlier-sensitivity", str(outlier_sensitivity),
        ]

    # Temporarily replace sys.argv so the CLI's argparse sees our arguments
    original_argv = sys.argv
    try:
        sys.argv = args
        sharp_frames_main()
    finally:
        sys.argv = original_argv

    frames = list(output_path.glob(f"*.{fmt}"))
    return len(frames)