#!/usr/bin/env python3
"""
build.py
Automates the PyInstaller build for the Video→COLMAP pipeline.

Prerequisites:
  pip install pyinstaller sharp-frames

  Download a static FFmpeg build from https://www.gyan.dev/ffmpeg/builds/
  (grab the "essentials" zip) and place ffmpeg.exe in a folder called
  ffmpeg/ next to this script.

Project layout expected:
  project/
  ├── build.py              ← this file
  ├── main.py
  ├── frame_selection.py
  ├── frame_to_colmap.py
  ├── export_config.xml
  └── ffmpeg/
      └── ffmpeg.exe
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FFMPEG_EXE = SCRIPT_DIR / "ffmpeg" / "ffmpeg.exe"


def check_prerequisites():
    errors = []

    if not (SCRIPT_DIR / "main.py").exists():
        errors.append("main.py not found in project root.")
    if not (SCRIPT_DIR / "export_config.xml").exists():
        errors.append("export_config.xml not found in project root.")
    if not FFMPEG_EXE.exists():
        errors.append(
            f"ffmpeg.exe not found at {FFMPEG_EXE}\n"
            "  Download from https://www.gyan.dev/ffmpeg/builds/ (essentials build),\n"
            "  extract, and place ffmpeg.exe in a ffmpeg/ folder next to this script."
        )

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


def find_tcl_tk_paths():
    """Locate Tcl/Tk DLLs and script libraries for Anaconda installs."""
    base = Path(sys.base_prefix)
    paths = {}

    # Anaconda keeps Tcl/Tk here
    lib_bin = base / "Library" / "bin"
    lib_lib = base / "Library" / "lib"

    # Standard (python.org) keeps them here
    std_dlls = base / "DLLs"
    std_tcl = base / "tcl"

    # Find the DLLs (tcl86t.dll, tk86t.dll)
    for search_dir in [lib_bin, std_dlls]:
        tcl_dll = list(search_dir.glob("tcl8*.dll"))
        tk_dll = list(search_dir.glob("tk8*.dll"))
        if tcl_dll and tk_dll:
            paths["dll_dir"] = search_dir
            break

    # Find the script libraries (tcl8.6/, tk8.6/)
    for search_dir in [lib_lib, std_tcl]:
        tcl_dirs = list(search_dir.glob("tcl8*"))
        tk_dirs = list(search_dir.glob("tk8*"))
        if tcl_dirs and tk_dirs:
            paths["tcl_lib"] = tcl_dirs[0]
            paths["tk_lib"] = tk_dirs[0]
            break

    return paths


def run_build():
    tcl_tk = find_tcl_tk_paths()

    if not tcl_tk.get("dll_dir"):
        print("[WARN] Could not find Tcl/Tk DLLs — the build may fail at runtime.")
    else:
        print(f"[INFO] Tcl/Tk DLLs: {tcl_tk['dll_dir']}")
        print(f"[INFO] Tcl scripts: {tcl_tk.get('tcl_lib', 'not found')}")

    cmd = [
        "pyinstaller",
        "--name", "VideoToColmap",
        "--onedir",
        "--windowed",           # no console window for the Tkinter app
        "--noconfirm",          # overwrite previous build without asking

        # Bundle FFmpeg alongside the exe
        "--add-data", f"{FFMPEG_EXE};ffmpeg",

        # Bundle the default export config
        "--add-data", f"{SCRIPT_DIR / 'export_config.xml'};.",

        # Hidden imports that PyInstaller might miss
        "--hidden-import", "frame_selection",
        "--hidden-import", "frame_to_colmap",
    ]

    # Add Tcl/Tk binaries and scripts for Anaconda compatibility
    if tcl_tk.get("dll_dir"):
        for dll in tcl_tk["dll_dir"].glob("tcl8*.dll"):
            cmd += ["--add-binary", f"{dll};."]
        for dll in tcl_tk["dll_dir"].glob("tk8*.dll"):
            cmd += ["--add-binary", f"{dll};."]
    if tcl_tk.get("tcl_lib"):
        cmd += ["--add-data", f"{tcl_tk['tcl_lib']};tcl/{tcl_tk['tcl_lib'].name}"]
    if tcl_tk.get("tk_lib"):
        cmd += ["--add-data", f"{tcl_tk['tk_lib']};tk/{tcl_tk['tk_lib'].name}"]

    cmd.append(str(SCRIPT_DIR / "main.py"))

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