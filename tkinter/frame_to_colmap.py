#!/usr/bin/env python3
"""
frame_to_colmap.py
Runs RealityScan CLI to align frames and export COLMAP registration data.
"""

import subprocess
from pathlib import Path


def run_colmap_export(
    rs_exe_path: str,
    images_path: str,
    output_path: str,
    export_config_path: str,
) -> None:
    """
    Run RealityScan to align images and export COLMAP text format.
    Raises subprocess.CalledProcessError on failure.
    """
    rs_exe = Path(rs_exe_path)
    images = Path(images_path)
    output = Path(output_path)
    config = Path(export_config_path)

    if not rs_exe.exists():
        raise FileNotFoundError(f"RealityScan executable not found: {rs_exe}")
    if not images.exists():
        raise FileNotFoundError(f"Images folder not found: {images}")
    if not config.exists():
        raise FileNotFoundError(f"Export config not found: {config}")

    output.mkdir(parents=True, exist_ok=True)

    registration_path = str(output / "registration")

    cmd = [
        str(rs_exe),
        "-addFolder", str(images),
        "-align",
        "-exportRegistration", registration_path, str(config),
        "-quit",
    ]

    subprocess.run(cmd, check=True)