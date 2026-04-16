#!/usr/bin/env python3
"""
build.py
Automates the PyInstaller build for the Video→COLMAP pipeline.

Prerequisites:
  pip install pyinstaller sharp-frames
  FFmpeg must be installed and available on the system PATH.

Project layout expected:
  project/
  ├── build.py              ← this file
  ├── main.py
  ├── frame_selection.py
  ├── frame_to_colmap.py
  └── export_config.xml
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def check_prerequisites():
    errors = []

    if not (SCRIPT_DIR / "main.py").exists():
        errors.append("main.py not found in project root.")
    if not (SCRIPT_DIR / "export_config.xml").exists():
        errors.append("export_config.xml not found in project root.")

    # Check sharp-frames is importable (needed so PyInstaller can find it)
    try:
        import sharp_frames  # noqa: F401
    except ImportError:
        errors.append("sharp-frames not installed. Run: pip install sharp-frames")

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        errors.append("PyInstaller not installed. Run: pip install pyinstaller")

    if errors:
        print("[ERROR] Prerequisites not met:\n")
        for e in errors:
            print(f"  • {e}\n")
        sys.exit(1)

    print("[OK] All prerequisites found.")


def run_build():
    cmd = [
        "pyinstaller",
        "--name", "VideoToColmap",
        "--onedir",
        "--console",            # show console for debugging (change to --windowed for release)
        "--noconfirm",          # overwrite previous build without asking

        # Bundle the default export config
        "--add-data", f"{SCRIPT_DIR / 'export_config.xml'};.",

        # Hidden imports that PyInstaller might miss
        "--hidden-import", "frame_selection",
        "--hidden-import", "frame_to_colmap",
        "--hidden-import", "sharp_frames",
        "--hidden-import", "sharp_frames.sharp_frames",
        "--collect-all", "sharp_frames",

        str(SCRIPT_DIR / "main.py"),
    ]

    print(f"\n[INFO] Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(SCRIPT_DIR))

    if result.returncode == 0:
        dist = SCRIPT_DIR / "dist" / "VideoToColmap"
        print(f"\n[DONE] Build complete!")
        print(f"  Output: {dist}")
        print(f"  Run:    {dist / 'VideoToColmap.exe'}")
    else:
        print(f"\n[ERROR] PyInstaller exited with code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    check_prerequisites()
    run_build()
