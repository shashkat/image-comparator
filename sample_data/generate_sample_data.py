"""Generate dummy plot collections for manually testing image-comparator.

Run from anywhere (needs matplotlib + numpy, already dependencies of the app):

    python sample_data/generate_sample_data.py

Every plot is synthetic. Each sample gets its own random seed, so the same sample
looks consistent across plot types (e.g. a low-quality sample has few genes per cell
in the QC plot AND a muddier UMAP), which makes it easy to spot when panels drift
out of sync. Re-running the script wipes and regenerates both scenario directories.
"""

import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
N_SAMPLES = 12
SAMPLES = [f"sample_{i:02d}" for i in range(1, N_SAMPLES + 1)]

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"
GRID = "#e4e3df"
CRITICAL = "#e34948"
GENES = ["CD3E", "CD19", "LYZ", "NKG7", "MS4A1", "GNLY", "PPBP", "FCGR3A"]

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT_SECONDARY,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": TEXT_SECONDARY,
    "ytick.color": TEXT_SECONDARY,
    "font.size": 11,
})


def sample_profile(sample):
    """Per-sample traits shared by every plot type."""
    idx = SAMPLES.index(sample)
    rng = np.random.default_rng(1000 + idx)
    return {
        "idx": idx,
        "rng": rng,
        "quality": rng.uniform(0.3, 1.0),  # drives QC depth and cluster crispness
        "n_clusters": int(rng.integers(3, 9)),
        "expr": rng.gamma(2.0, 1.5, size=len(GENES)),
    }


HEADER_IN = 0.95  # header height in inches, fixed so very tall/wide figures keep a normal-looking title


def header_top(fig):
    """Figure fraction below the header, for tight_layout(rect=...)."""
    return 1 - HEADER_IN / fig.get_size_inches()[1]


def title(fig, sample, plot_type, profile):
    w, h = fig.get_size_inches()
    x = 0.15 / w
    fig.text(x, 1 - 0.1 / h, sample, ha="left", va="top", fontsize=20, fontweight="bold", color=TEXT_PRIMARY)
    fig.text(x, 1 - 0.55 / h, f"{plot_type}  ·  index {profile['idx'] + 1}/{N_SAMPLES}  ·  quality {profile['quality']:.2f}",
             ha="left", va="top", fontsize=11, color=TEXT_SECONDARY)


def plot_qc(sample, path):
    p = sample_profile(sample)
    genes = p["rng"].lognormal(np.log(600 + 1800 * p["quality"]), 0.45, size=3000)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(genes, bins=60, color=SERIES[0], edgecolor=SURFACE, linewidth=0.6)
    ax.axvline(500, color=CRITICAL, lw=2, ls="--")
    ax.text(0.98, 0.95, "dashed line: min. genes cutoff (500)", transform=ax.transAxes, ha="right", color=TEXT_SECONDARY, fontsize=10)
    ax.set_xlabel("Genes detected per cell")
    ax.set_ylabel("Cells")
    title(fig, sample, "QC: genes per cell", p)
    fig.tight_layout(rect=(0, 0, 1, header_top(fig)))
    fig.savefig(path, dpi=90)
    plt.close(fig)


def plot_expression(sample, path):
    p = sample_profile(sample)
    order = np.argsort(p["expr"])
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(np.array(GENES)[order], p["expr"][order], color=SERIES[0], height=0.6)
    for y, v in enumerate(p["expr"][order]):
        ax.text(v + 0.1, y, f"{v:.1f}", va="center", fontsize=9, color=TEXT_SECONDARY)
    ax.set_xlabel("Mean log-normalised expression")
    ax.grid(axis="y", visible=False)
    title(fig, sample, "Marker gene expression", p)
    fig.tight_layout(rect=(0, 0, 1, header_top(fig)))
    fig.savefig(path, dpi=90)
    plt.close(fig)


def plot_umap(sample, path):
    p = sample_profile(sample)
    rng, k = p["rng"], p["n_clusters"]
    centers = rng.uniform(-8, 8, size=(k, 2))
    spread = 0.6 + 1.6 * (1 - p["quality"])
    fig, ax = plt.subplots(figsize=(7, 5))
    for c in range(k):
        pts = centers[c] + rng.normal(0, spread, size=(250, 2))
        ax.scatter(pts[:, 0], pts[:, 1], s=6, color=SERIES[c], alpha=0.75, linewidths=0, label=f"cluster {c}")
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False, markerscale=2.5, labelcolor=TEXT_SECONDARY)
    title(fig, sample, f"UMAP ({k} clusters)", p)
    fig.tight_layout(rect=(0, 0, 1, header_top(fig)))
    fig.savefig(path)
    plt.close(fig)


def plot_spatial(sample, path):
    p = sample_profile(sample)
    rng = p["rng"]
    y, x = np.mgrid[0:80, 0:80]
    field = np.zeros((80, 80))
    for _ in range(4):
        cx, cy, r = rng.uniform(10, 70), rng.uniform(10, 70), rng.uniform(6, 18)
        field += np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * r ** 2))
    field += rng.normal(0, 0.05 + 0.2 * (1 - p["quality"]), field.shape)
    fig, ax = plt.subplots(figsize=(6, 5.4))
    im = ax.imshow(field, cmap="Blues", origin="lower")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Signal density")
    title(fig, sample, "Spatial signal map", p)
    fig.tight_layout(rect=(0, 0, 1, header_top(fig)))
    fig.savefig(path, dpi=90, pil_kwargs={"quality": 90})
    plt.close(fig)


def plot_coverage_track(sample, path):
    """Very wide: a genome-browser style coverage track whose width varies per sample."""
    p = sample_profile(sample)
    rng = p["rng"]
    width = rng.uniform(14, 26)
    pos = np.linspace(0, 1.0, 4000)
    cov = np.convolve(rng.gamma(1 + 3 * p["quality"], 4, size=pos.size), np.ones(40) / 40, mode="same")
    fig, ax = plt.subplots(figsize=(width, 3.2))
    ax.fill_between(pos, cov, color=SERIES[0], alpha=0.35, linewidth=0)
    ax.plot(pos, cov, color=SERIES[0], lw=1)
    ax.set_xlim(pos[0], pos[-1])
    ax.set_ylim(bottom=0)
    ax.set_xlabel("chr1 position (Mb)")
    ax.set_ylabel("Coverage")
    title(fig, sample, f"Coverage track  ·  {width:.1f} × 3.2 in ({width / 3.2:.1f}:1)", p)
    fig.tight_layout(rect=(0, 0, 1, header_top(fig)))
    fig.savefig(path, dpi=80)
    plt.close(fig)


def plot_gene_dotplot(sample, path):
    """Very tall: a dot plot over many genes; gene count (and so height) varies per sample."""
    p = sample_profile(sample)
    rng = p["rng"]
    n_genes = int(rng.integers(35, 80))
    genes = [f"GENE_{i:02d}" for i in range(1, n_genes + 1)]
    cell_types = ["T cell", "B cell", "NK", "Mono"]
    frac = rng.beta(1.2, 2.5, size=(n_genes, len(cell_types)))
    expr = rng.gamma(2.0, 1.0, size=(n_genes, len(cell_types)))
    height = 0.22 * n_genes + 1.8
    fig, ax = plt.subplots(figsize=(4.5, height))
    xx, yy = np.meshgrid(np.arange(len(cell_types)), np.arange(n_genes))
    sc = ax.scatter(xx.ravel(), yy.ravel(), s=20 + 160 * frac.ravel(), c=expr.ravel(), cmap="Blues",
                    vmin=0, edgecolors=GRID, linewidths=0.5)
    ax.set_xticks(range(len(cell_types)), cell_types, rotation=45, ha="right")
    ax.set_yticks(range(n_genes), genes, fontsize=8)
    ax.set_xlim(-0.6, len(cell_types) - 0.4)
    ax.set_ylim(n_genes - 0.5, -0.5)
    fig.colorbar(sc, ax=ax, fraction=0.08, pad=0.04, label="Mean expression")
    title(fig, sample, f"{n_genes} genes", p)
    fig.tight_layout(rect=(0, 0, 1, header_top(fig)))
    fig.savefig(path, dpi=80)
    plt.close(fig)


# (width, height) in inches; consecutive samples jump between extremes
MIXED_SHAPES = [(7, 5), (24, 3.2), (4, 18), (7, 7), (28, 3), (4.5, 22)]


def plot_mixed_shape(sample, path):
    """Shape changes on every step, from square to very wide to very tall."""
    p = sample_profile(sample)
    w, h = MIXED_SHAPES[p["idx"] % len(MIXED_SHAPES)]
    walk = np.cumsum(p["rng"].normal(0, 1, size=600))
    fig, ax = plt.subplots(figsize=(w, h))
    if h > w:  # tall: run the trace down the page
        ax.plot(walk, np.arange(walk.size), color=SERIES[2], lw=2)
        ax.invert_yaxis()
        ax.set_xlabel("Signal")
        ax.set_ylabel("Time step")
    else:
        ax.plot(np.arange(walk.size), walk, color=SERIES[2], lw=2)
        ax.set_xlabel("Time step")
        ax.set_ylabel("Signal")
    ratio = f"{w / h:.1f}:1" if w >= h else f"1:{h / w:.1f}"
    title(fig, sample, f"{w} × {h} in ({ratio})", p)
    fig.tight_layout(rect=(0, 0, 1, header_top(fig)))
    fig.savefig(path)
    plt.close(fig)


# scenario 1: every directory has every sample, mixed file formats
COMPLETE = {
    "qc_plots": (plot_qc, ".png"),
    "expression_plots": (plot_expression, ".png"),
    "umap_plots": (plot_umap, ".pdf"),
    "spatial_plots": (plot_spatial, ".jpg"),
}

# scenario 2: directories with gaps and mixed extensions, for "Sync Directories Now"
# (plot fn, missing samples, main extension, {sample: other extension})
WITH_GAPS = {
    "qc_plots": (plot_qc, {"sample_03", "sample_08"}, ".png",
                 {"sample_02": ".jpg", "sample_07": ".pdf"}),
    "expression_plots": (plot_expression, {"sample_05"}, ".jpg",
                         {"sample_04": ".png", "sample_09": ".png", "sample_12": ".pdf"}),
    "umap_plots": (plot_umap, {"sample_01", "sample_10", "sample_11"}, ".pdf",
                   {"sample_03": ".png", "sample_06": ".jpg"}),
}


def plot_dense_scatter(sample, path):
    """Vector-heavy: every point is a separate PDF path, so rasterising is slow at any DPI."""
    p = sample_profile(sample)
    rng = p["rng"]
    n = int(rng.integers(60, 221)) * 1000
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(*rng.normal(size=(2, n)), s=2, c=rng.random(n), cmap="Blues", vmin=-0.3, linewidths=0)
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    title(fig, sample, f"Dense scatter ({n // 1000}k points)", p)
    fig.tight_layout(rect=(0, 0, 1, header_top(fig)))
    fig.savefig(path)
    plt.close(fig)


def plot_dense_mesh(sample, path):
    """Vector-heavy: a pcolormesh is stored as one PDF quad per cell."""
    p = sample_profile(sample)
    rng = p["rng"]
    side = int(rng.integers(250, 451))
    fig, ax = plt.subplots(figsize=(8, 6))
    mesh = ax.pcolormesh(rng.random((side, side)), cmap="Blues")
    ax.grid(False)
    fig.colorbar(mesh, ax=ax, label="Value")
    title(fig, sample, f"Dense mesh ({side} × {side} cells)", p)
    fig.tight_layout(rect=(0, 0, 1, header_top(fig)))
    fig.savefig(path)
    plt.close(fig)


def plot_large_page(sample, path):
    """Pixel-heavy: a physically large page, so the rendered image gets huge at high DPI."""
    p = sample_profile(sample)
    rng = p["rng"]
    side = int(rng.integers(20, 37))
    fig, ax = plt.subplots(figsize=(side, side))
    for i, walk in enumerate(np.cumsum(rng.normal(size=(8, 2000)), axis=1)):
        ax.plot(walk, color=SERIES[i], lw=2)
    ax.set_xlabel("Time step")
    ax.set_ylabel("Signal")
    title(fig, sample, f"Large page ({side} × {side} in)", p)
    fig.tight_layout(rect=(0, 0, 1, header_top(fig)))
    fig.savefig(path)
    plt.close(fig)


# scenario 3: extreme and changing aspect ratios, for zoom / reset-view behaviour
VARIED_ASPECT = {
    "wide_plots": (plot_coverage_track, ".png"),
    "tall_plots": (plot_gene_dotplot, ".png"),
    "mixed_shape_plots": (plot_mixed_shape, ".pdf"),
    "regular_plots": (plot_qc, ".png"),
}

# scenario 4: PDFs that are slow to rasterise, for PDF rendering speed (~100 MB, git-ignored)
HEAVY_PDF = {
    "dense_scatter_plots": plot_dense_scatter,
    "dense_mesh_plots": plot_dense_mesh,
    "large_page_plots": plot_large_page,
    "regular_plots": plot_umap,
}


def reset(directory):
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)


def main():
    complete_root = ROOT / "complete"
    reset(complete_root)
    for dirname, (plot_fn, ext) in COMPLETE.items():
        (complete_root / dirname).mkdir()
        for sample in SAMPLES:
            plot_fn(sample, complete_root / dirname / f"{sample}{ext}")

    gaps_root = ROOT / "with_gaps"
    reset(gaps_root)
    for dirname, (plot_fn, missing, main_ext, other_exts) in WITH_GAPS.items():
        (gaps_root / dirname).mkdir()
        for sample in SAMPLES:
            if sample not in missing:
                plot_fn(sample, gaps_root / dirname / f"{sample}{other_exts.get(sample, main_ext)}")

    aspect_root = ROOT / "varied_aspect"
    reset(aspect_root)
    for dirname, (plot_fn, ext) in VARIED_ASPECT.items():
        (aspect_root / dirname).mkdir()
        for sample in SAMPLES:
            plot_fn(sample, aspect_root / dirname / f"{sample}{ext}")

    heavy_root = ROOT / "heavy_pdf"
    reset(heavy_root)
    for dirname, plot_fn in HEAVY_PDF.items():
        (heavy_root / dirname).mkdir()
        for sample in SAMPLES:
            plot_fn(sample, heavy_root / dirname / f"{sample}.pdf")

    print(f"Wrote sample plots to {complete_root}, {gaps_root}, {aspect_root} and {heavy_root}")


if __name__ == "__main__":
    main()
