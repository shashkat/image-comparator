# Sample data

Synthetic plots for manually testing image-comparator. Every plot shows its sample ID in large text, plus its position (`index n/12`) and a per-sample "quality" score. The same sample has the same quality score in every plot type, so you can see right away when the panels drift out of sync.

Regenerate (this wipes and recreates `complete/` and `with_gaps/`, including any sync placeholders):

```sh
python sample_data/generate_sample_data.py   # needs matplotlib + numpy
```

## `complete/`: every directory has every sample

| Directory | Format | Plot |
|---|---|---|
| `qc_plots/` | `.png` | genes-per-cell histogram |
| `expression_plots/` | `.png` | marker gene bar chart |
| `umap_plots/` | `.pdf` | clustered scatter (tests the PDF DPI setting) |
| `spatial_plots/` | `.jpg` | heatmap |

Use this for the basic workflow: synchronised navigation, a 2×2 grid, reordering, the custom starting index, and PDF DPI.

## `with_gaps/`: directories with missing samples (all `.png`)

| Directory | Missing |
|---|---|
| `qc_plots/` | sample_03, sample_08 |
| `expression_plots/` | sample_05 |
| `umap_plots/` | sample_01, sample_10, sample_11 |

Start the comparator without syncing and the panels drift apart (the sample IDs stop matching). Click **Sync Directories Now** and 6 placeholders are created, after which navigation stays aligned. Run the script again to restore the gaps.

## `varied_aspect/`: very wide, very tall, and shape-changing plots

| Directory | Format | Shape |
|---|---|---|
| `wide_plots/` | `.png` | coverage tracks, 14–26 in wide × 3.2 in tall (up to ~8:1); width changes per sample |
| `tall_plots/` | `.png` | gene dot plots, 4.5 in wide × 9–19 in tall (up to ~1:4); height changes per sample |
| `mixed_shape_plots/` | `.pdf` | cycles 7×5 → 24×3.2 → 4×18 → 7×7 → 28×3 → 4.5×22, so every step changes shape |
| `regular_plots/` | `.png` | the normal 7×5 QC histogram, as a reference panel |

Each header shows the figure's size and aspect ratio. Use this set for zooming, panning and the toolbar's Home button. Zoom in on a plot, move to the next sample, then press Home: the view should reset to the *current* plot, not to an earlier one.
