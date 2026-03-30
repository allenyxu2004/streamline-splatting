#!/usr/bin/env python3
"""
main.py
Tkinter UI for the Video → Sharp Frames → COLMAP pipeline.
"""

import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from frame_selection import run_frame_selection
from frame_to_colmap import run_colmap_export

# ─── Resolve bundled export_config.xml next to this script ────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_EXPORT_CONFIG = SCRIPT_DIR / "export_config.xml"


class PipelineApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video → COLMAP Pipeline")
        self.resizable(False, False)

        self._running = False
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        pad = dict(padx=8, pady=4)

        # ── Paths section ─────────────────────────────────────────────────
        path_frame = ttk.LabelFrame(self, text="Paths", padding=8)
        path_frame.grid(row=0, column=0, sticky="ew", **pad)

        self.input_video_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.rs_exe_var = tk.StringVar()
        self.config_var = tk.StringVar(value=str(DEFAULT_EXPORT_CONFIG))

        self._path_row(path_frame, 0, "Input Video:", self.input_video_var, self._browse_video)
        self._path_row(path_frame, 1, "Output Folder:", self.output_dir_var, self._browse_output)
        self._path_row(path_frame, 2, "RealityScan Exe:", self.rs_exe_var, self._browse_rs_exe)
        self._path_row(path_frame, 3, "Export Config:", self.config_var, self._browse_config)

        # ── Frame extraction section ──────────────────────────────────────
        extract_frame = ttk.LabelFrame(self, text="Frame Extraction", padding=8)
        extract_frame.grid(row=1, column=0, sticky="ew", **pad)

        r = 0
        ttk.Label(extract_frame, text="FPS:").grid(row=r, column=0, sticky="w")
        self.fps_var = tk.IntVar(value=10)
        ttk.Spinbox(extract_frame, from_=1, to=60, textvariable=self.fps_var, width=6).grid(row=r, column=1, sticky="w")

        ttk.Label(extract_frame, text="Format:").grid(row=r, column=2, sticky="w", padx=(16, 0))
        self.format_var = tk.StringVar(value="jpg")
        ttk.Combobox(extract_frame, textvariable=self.format_var, values=["jpg", "png"], state="readonly", width=5).grid(row=r, column=3, sticky="w")

        ttk.Label(extract_frame, text="Width (0=orig):").grid(row=r, column=4, sticky="w", padx=(16, 0))
        self.width_var = tk.IntVar(value=0)
        ttk.Spinbox(extract_frame, from_=0, to=7680, increment=100, textvariable=self.width_var, width=7).grid(row=r, column=5, sticky="w")

        # ── Selection method section ──────────────────────────────────────
        method_frame = ttk.LabelFrame(self, text="Selection Method", padding=8)
        method_frame.grid(row=2, column=0, sticky="ew", **pad)

        self.method_var = tk.StringVar(value="batched")
        method_combo = ttk.Combobox(
            method_frame, textvariable=self.method_var,
            values=["best-n", "batched", "outlier-removal"],
            state="readonly", width=18,
        )
        method_combo.grid(row=0, column=0, columnspan=2, sticky="w")
        method_combo.bind("<<ComboboxSelected>>", lambda _: self._refresh_method_params())

        # Container for method-specific params
        self.param_container = ttk.Frame(method_frame)
        self.param_container.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(6, 0))

        # best-n params
        self.num_frames_var = tk.IntVar(value=300)
        self.min_buffer_var = tk.IntVar(value=3)

        # batched params
        self.batch_size_var = tk.IntVar(value=5)
        self.batch_buffer_var = tk.IntVar(value=2)

        # outlier-removal params
        self.outlier_window_var = tk.IntVar(value=15)
        self.outlier_sensitivity_var = tk.IntVar(value=60)

        self._refresh_method_params()

        # ── Run button + status ───────────────────────────────────────────
        action_frame = ttk.Frame(self, padding=8)
        action_frame.grid(row=3, column=0, sticky="ew", **pad)

        self.run_btn = ttk.Button(action_frame, text="Run Pipeline", command=self._run_pipeline)
        self.run_btn.grid(row=0, column=0)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(action_frame, textvariable=self.status_var, foreground="gray").grid(row=0, column=1, padx=(12, 0))

        self.progress = ttk.Progressbar(action_frame, mode="indeterminate", length=200)
        self.progress.grid(row=0, column=2, padx=(12, 0))

    # ── Helpers ───────────────────────────────────────────────────────────

    def _path_row(self, parent, row, label, var, command):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=var, width=55).grid(row=row, column=1, sticky="ew", padx=(4, 4))
        ttk.Button(parent, text="Browse…", command=command).grid(row=row, column=2)

    def _browse_video(self):
        p = filedialog.askopenfilename(
            title="Select input video",
            filetypes=[("Video files", "*.mov *.mp4 *.avi *.mkv *.webm"), ("All", "*.*")],
        )
        if p:
            self.input_video_var.set(p)

    def _browse_output(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p:
            self.output_dir_var.set(p)

    def _browse_rs_exe(self):
        p = filedialog.askopenfilename(
            title="Select RealityScan executable",
            filetypes=[("Executable", "*.exe"), ("All", "*.*")],
        )
        if p:
            self.rs_exe_var.set(p)

    def _browse_config(self):
        p = filedialog.askopenfilename(
            title="Select export config XML",
            filetypes=[("XML", "*.xml"), ("All", "*.*")],
        )
        if p:
            self.config_var.set(p)

    def _refresh_method_params(self):
        for w in self.param_container.winfo_children():
            w.destroy()

        method = self.method_var.get()
        f = self.param_container

        if method == "best-n":
            ttk.Label(f, text="Num Frames:").grid(row=0, column=0, sticky="w")
            ttk.Spinbox(f, from_=10, to=5000, textvariable=self.num_frames_var, width=7).grid(row=0, column=1, sticky="w", padx=(4, 16))
            ttk.Label(f, text="Min Buffer:").grid(row=0, column=2, sticky="w")
            ttk.Spinbox(f, from_=0, to=100, textvariable=self.min_buffer_var, width=5).grid(row=0, column=3, sticky="w")

        elif method == "batched":
            ttk.Label(f, text="Batch Size:").grid(row=0, column=0, sticky="w")
            ttk.Spinbox(f, from_=1, to=100, textvariable=self.batch_size_var, width=5).grid(row=0, column=1, sticky="w", padx=(4, 16))
            ttk.Label(f, text="Batch Buffer:").grid(row=0, column=2, sticky="w")
            ttk.Spinbox(f, from_=0, to=100, textvariable=self.batch_buffer_var, width=5).grid(row=0, column=3, sticky="w")

        elif method == "outlier-removal":
            ttk.Label(f, text="Window Size:").grid(row=0, column=0, sticky="w")
            ttk.Spinbox(f, from_=1, to=100, textvariable=self.outlier_window_var, width=5).grid(row=0, column=1, sticky="w", padx=(4, 16))
            ttk.Label(f, text="Sensitivity (0–100):").grid(row=0, column=2, sticky="w")
            ttk.Spinbox(f, from_=0, to=100, textvariable=self.outlier_sensitivity_var, width=5).grid(row=0, column=3, sticky="w")

    # ── Pipeline execution ────────────────────────────────────────────────

    def _set_status(self, msg, color="gray"):
        self.status_var.set(msg)
        for w in self.winfo_children():
            pass  # status label color updated below
        # Find the status label and update color
        self.after(0, lambda: None)  # ensure we're on main thread
        self.status_var.set(msg)

    def _validate(self) -> bool:
        if not self.input_video_var.get():
            messagebox.showerror("Missing field", "Please select an input video.")
            return False
        if not Path(self.input_video_var.get()).exists():
            messagebox.showerror("Not found", "Input video file does not exist.")
            return False
        if not self.output_dir_var.get():
            messagebox.showerror("Missing field", "Please select an output folder.")
            return False
        if not self.rs_exe_var.get():
            messagebox.showerror("Missing field", "Please select the RealityScan executable.")
            return False
        if not Path(self.rs_exe_var.get()).exists():
            messagebox.showerror("Not found", "RealityScan executable does not exist.")
            return False
        if not self.config_var.get():
            messagebox.showerror("Missing field", "Please select an export config XML.")
            return False
        if not Path(self.config_var.get()).exists():
            messagebox.showerror("Not found", "Export config XML does not exist.")
            return False
        return True

    def _run_pipeline(self):
        if self._running:
            return
        if not self._validate():
            return

        self._running = True
        self.run_btn.configure(state="disabled")
        self.progress.start(15)
        self.status_var.set("Step 1/2 — Extracting sharp frames…")

        thread = threading.Thread(target=self._pipeline_worker, daemon=True)
        thread.start()

    def _pipeline_worker(self):
        input_video = self.input_video_var.get()
        output_dir = self.output_dir_var.get()
        rs_exe = self.rs_exe_var.get()
        config = self.config_var.get()

        # Intermediate frames folder: sibling of the input video
        video_parent = Path(input_video).parent
        intermediate_dir = video_parent / "_intermediate_frames"

        try:
            # ── Step 1: frame extraction ──────────────────────────────────
            n = run_frame_selection(
                input_video=input_video,
                output_dir=str(intermediate_dir),
                fps=self.fps_var.get(),
                fmt=self.format_var.get(),
                width=self.width_var.get(),
                selection_method=self.method_var.get(),
                num_frames=self.num_frames_var.get(),
                min_buffer=self.min_buffer_var.get(),
                batch_size=self.batch_size_var.get(),
                batch_buffer=self.batch_buffer_var.get(),
                outlier_window=self.outlier_window_var.get(),
                outlier_sensitivity=self.outlier_sensitivity_var.get(),
            )
            self.after(0, lambda: self.status_var.set(
                f"Step 2/2 — Running COLMAP export ({n} frames)…"
            ))

            # ── Step 2: COLMAP export ─────────────────────────────────────
            run_colmap_export(
                rs_exe_path=rs_exe,
                images_path=str(intermediate_dir),
                output_path=output_dir,
                export_config_path=config,
            )

            # ── Cleanup intermediate frames ───────────────────────────────
            shutil.rmtree(intermediate_dir, ignore_errors=True)

            self.after(0, lambda: self._finish_success(output_dir))

        except Exception as e:
            self.after(0, lambda: self._finish_error(str(e)))

    def _finish_success(self, output_dir):
        self.progress.stop()
        self.status_var.set(f"Done — output in {output_dir}")
        self.run_btn.configure(state="normal")
        self._running = False
        messagebox.showinfo("Pipeline complete", f"COLMAP data exported to:\n{output_dir}")

    def _finish_error(self, err):
        self.progress.stop()
        self.status_var.set("Error — see details")
        self.run_btn.configure(state="normal")
        self._running = False
        messagebox.showerror("Pipeline failed", err)


if __name__ == "__main__":
    app = PipelineApp()
    app.mainloop()