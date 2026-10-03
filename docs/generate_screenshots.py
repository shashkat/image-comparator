#!/usr/bin/env python3
"""
Generate the screenshots used by the website (docs/index.html) from sample_data/.

Run from the repository root (needs the package's dependencies, and macOS for the
start-window screenshot):

    python docs/generate_screenshots.py              # all screenshots
    python docs/generate_screenshots.py resize zoom  # only some of them

The plot-window screenshots are rendered without opening a window. The start window is
opened briefly and captured with macOS's screencapture.
"""

import glob
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

import matplotlib.pyplot as plt
from PIL import Image

from image_comparator import app

ASSETS = ROOT / 'docs' / 'assets'
SAMPLES = ROOT / 'sample_data'
DPI = 80


def first(directory, n=0):
    return sorted(glob.glob(str(directory / '*')))[n]


def save(fig, name, dpi=DPI, **kwargs):
    """Save a figure as WebP (much smaller than PNG at the same quality)."""
    tmp = ASSETS / f'{name}.png'
    fig.savefig(tmp, dpi=dpi, **kwargs)
    Image.open(tmp).convert('RGB').save(ASSETS / f'{name}.webp', quality=88, method=6)
    tmp.unlink()


def frame(fig):
    fig.canvas.draw()
    return Image.frombuffer('RGBA', fig.canvas.get_width_height(physical=True),
                            fig.canvas.buffer_rgba()).convert('RGB')


def navigation():
    """Animated 2x2 grid stepping through samples, all panels moving together."""
    dirs = ['qc_plots', 'expression_plots', 'umap_plots', 'spatial_plots']
    c = app.ImageComparator([first(SAMPLES / 'complete' / d) for d in dirs], num_cols=2)
    c.fig.set_dpi(DPI)
    frames = []
    for _ in range(5):
        frames.append(frame(c.fig))
        c.indices = [i + 1 for i in c.indices]
        c.update_display()
    frames[0].save(ASSETS / 'navigation.webp', save_all=True, append_images=frames[1:],
                   duration=1400, loop=0, quality=85, method=6)
    frames[0].save(ASSETS / 'hero.webp', quality=88, method=6)
    c.pdf_cache.shutdown()
    plt.close(c.fig)


def sync():
    """The same step before and after syncing directories that have missing samples."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        dirs = ['qc_plots', 'expression_plots', 'umap_plots']
        for d in dirs:
            shutil.copytree(SAMPLES / 'with_gaps' / d, tmp / d)

        def shot(name):
            c = app.ImageComparator([first(tmp / d) for d in dirs], num_cols=3)
            c.fig.set_size_inches(18, 5)
            c.indices = [i + 2 for i in c.indices]
            c.update_display()
            save(c.fig, name)
            c.pdf_cache.shutdown()
            plt.close(c.fig)

        shot('sync-before')
        # Create placeholders the way "Sync Directories Now" does
        stems = sorted({Path(f).stem for d in dirs for f in glob.glob(str(tmp / d / '*'))})
        for d in dirs:
            files = sorted((tmp / d).iterdir())
            ext = max({f.suffix for f in files}, key=[f.suffix for f in files].count)
            for stem in sorted(set(stems) - {f.stem for f in files}):
                path = tmp / d / f'{stem}{ext}'
                if ext == '.pdf':
                    app.ConfigDialog._create_placeholder_pdf(None, path, path.name)
                else:
                    app.ConfigDialog._create_placeholder_image(None, path, path.name)
        shot('sync-after')


def resize():
    """Very wide and very tall plots, with equal panels and after dragging the gaps."""
    dirs = ['wide_plots', 'regular_plots', 'tall_plots', 'mixed_shape_plots']
    c = app.ImageComparator([first(SAMPLES / 'varied_aspect' / d) for d in dirs], num_cols=2)
    save(c.fig, 'resize-before')
    c.width_ratios = [[2.6, 1.0], [0.45, 1.55]]
    c.height_ratios = [0.6, 1.4]
    c._apply_ratios()
    c._hover = {'kind': 'col', 'row': 0, 'index': 0}
    save(c.fig, 'resize-after')
    c.pdf_cache.shutdown()
    plt.close(c.fig)


def zoom():
    """A PDF zoomed in about 6x, before and after the visible region is re-rendered."""
    import time
    c = app.ImageComparator([first(SAMPLES / 'complete' / 'umap_plots')], num_cols=1)
    ax = c.axes[0]
    h, w = ax.images[0].get_array().shape[:2]
    ax.set_xlim(w * 0.30, w * 0.30 + w / 6)
    ax.set_ylim(h * 0.45 + h / 6, h * 0.45)
    c.fig.canvas.draw()
    box = ax.get_window_extent().transformed(c.fig.dpi_scale_trans.inverted())
    save(c.fig, 'zoom-before', dpi=c.fig.dpi, bbox_inches=box)
    for _ in range(200):
        c._update_zoom_renders()
        if not c._zoom_wanted:
            break
        time.sleep(0.05)
    save(c.fig, 'zoom-after', dpi=c.fig.dpi, bbox_inches=box)
    c.pdf_cache.shutdown()
    plt.close(c.fig)


def start_window():
    """The start window with three plot collections added (macOS only)."""
    if sys.platform != 'darwin':
        print('Skipping the start-window screenshot (needs macOS)')
        return
    import os
    os.chdir(ROOT)  # paths relative to the repository, so the file list doesn't show your home directory
    dialog = app.ConfigDialog()
    dialog.selected_files = [os.path.relpath(first(SAMPLES / 'complete' / d), ROOT)
                             for d in ['qc_plots', 'expression_plots', 'umap_plots', 'spatial_plots']]
    dialog._refresh_listbox()
    dialog._update_starting_index()
    dialog.num_cols.set(2)
    root = dialog.root
    root.attributes('-topmost', True)
    root.update()
    root.after(800)
    root.update()
    x, y, width, height = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
    out = ASSETS / 'start-window.png'
    result = subprocess.run(['screencapture', '-x', '-R', f'{x},{y},{width},{height}', str(out)])
    root.destroy()
    if result.returncode != 0:
        print('Could not capture the start window: allow Screen Recording for your terminal in '
              'System Settings > Privacy & Security, then run: python docs/generate_screenshots.py start_window')
        return
    Image.open(out).convert('RGB').save(ASSETS / 'start-window.webp', quality=90, method=6)
    out.unlink()


if __name__ == '__main__':
    plt.switch_backend('Agg')
    ASSETS.mkdir(exist_ok=True)
    steps = [navigation, sync, resize, zoom, start_window]
    # Optionally generate only some screenshots, e.g.: python docs/generate_screenshots.py zoom start_window
    if len(sys.argv) > 1:
        steps = [step for step in steps if step.__name__ in sys.argv[1:]]
    for step in steps:
        print(f'Generating {step.__name__}...')
        step()
    print(f'Screenshots written to {ASSETS}')
