# Sample data

Synthetic plots for manually testing image-comparator. Every plot shows its sample ID in large text, plus its position (`index n/12`) and a per-sample "quality" score. The same sample has the same quality score in every plot type, so you can see right away when the panels drift out of sync.

Regenerate (this wipes and recreates `complete/`, `with_gaps/` and `varied_aspect/`, including any sync placeholders):

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

## `with_gaps/`: directories with missing samples and mixed extensions

| Directory | Missing | Main extension | Other extensions |
|---|---|---|---|
| `qc_plots/` | sample_03, sample_08 | `.png` | sample_02 `.jpg`, sample_07 `.pdf` |
| `expression_plots/` | sample_05 | `.jpg` | sample_04 `.png`, sample_09 `.png`, sample_12 `.pdf` |
| `umap_plots/` | sample_01, sample_10, sample_11 | `.pdf` | sample_03 `.png`, sample_06 `.jpg` |

Start the comparator without syncing and the panels drift apart (the sample IDs stop matching). Click **Sync Directories Now** and 6 placeholders are created, each using its directory's main extension, after which navigation stays aligned. Sync matches filenames without their extensions, so `sample_02.jpg` and `sample_02.pdf` count as the same sample. Run the script again to restore the gaps.

## `varied_aspect/`: very wide, very tall, and shape-changing plots

| Directory | Format | Shape |
|---|---|---|
| `wide_plots/` | `.png` | coverage tracks, 14–26 in wide × 3.2 in tall (up to ~8:1); width changes per sample |
| `tall_plots/` | `.png` | gene dot plots, 4.5 in wide × 9–19 in tall (up to ~1:4); height changes per sample |
| `mixed_shape_plots/` | `.pdf` | cycles 7×5 → 24×3.2 → 4×18 → 7×7 → 28×3 → 4.5×22, so every step changes shape |
| `regular_plots/` | `.png` | the normal 7×5 QC histogram, as a reference panel |

Each header shows the figure's size and aspect ratio. Use this set for zooming, panning and the toolbar's Home button. Zoom in on a plot, move to the next sample, then press Home: the view should reset to the *current* plot, not to an earlier one.
