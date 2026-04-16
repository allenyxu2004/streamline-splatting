# Video → COLMAP Pipeline

Converts a video file into COLMAP-format camera registration data by extracting sharp frames and running them through RealityScan alignment.

## Prerequisites

- **FFmpeg** — must be installed and accessible on your system PATH. Download from [ffmpeg.org](https://ffmpeg.org/download.html) and follow your OS's instructions for adding it to PATH.
- **RealityScan** — expected at `C:\Program Files\Epic Games\RealityScan_2.1\RealityScan.exe`. If installed elsewhere, you can point to the executable manually (see below).

## Setup

1. Extract `dist.zip` to a location of your choice.
2. Open the extracted `VideoToColmap` folder and run `VideoToColmap.exe`.

## Usage

Fill in the fields in the application window:

| Field | Description |
|---|---|
| **Input Video** | The video file to process (`.mov`, `.mp4`, `.avi`, `.mkv`, `.webm`) |
| **Output Folder** | Where the final COLMAP registration data will be written |
| **RealityScan Exe** | Path to `RealityScan.exe` — browse if not at the default location |
| **Export Config** | Pre-filled with the bundled `export_config.xml`; leave as-is unless you have a custom config |

Configure frame extraction as needed:

- **FPS** — how many frames per second to sample from the video (default: 10)
- **Format** — output frame format: `jpg` or `png`
- **Width** — resize frames to this width in pixels; set to `0` to keep original resolution

Choose a **Selection Method** to control how the sharpest frames are picked:

- `batched` *(default)* — divides frames into batches and picks the sharpest from each
- `best-n` — picks the top N sharpest frames globally
- `outlier-removal` — removes blurry outliers based on a sliding window

Click **Run Pipeline**. The app will extract frames, run RealityScan alignment, and write the COLMAP output to your chosen output folder. Intermediate frames are cleaned up automatically when the pipeline finishes.
