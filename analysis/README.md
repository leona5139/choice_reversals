# Analysis

Edit `run_analysis/pilot_1.py` to select players from `pilot_1`, add notes, or set
`ANALYSIS_ORDER`: `[]` runs all; `[2, 1]` runs Figure 2 then Figure 1.

From the repository folder:

```sh
uv run python -m analysis.run_analysis.pilot_1
```

Each run writes the selected outputs to `output/analysis/pilot_1/`.

- `metadata.json`: notes, timestamp, selected players, and files updated this run.
- `decisions.csv`: every player's rounds, allocations, and choice categories.
- `00_overview.csv`: counts by model setup, treatment, and task.
- `01_fig1_choices.csv` / `.png`: pure A/P treatments, rounds 1–4.
- `02_fig2_choices.csv` / `.png`: all treatments, rounds 1–2, 3–4, and 5–8.
- `03_fig3_revisions.csv` / `.png`: initial choices, final choices, and changes in rounds 5–8 of `4A_4AR`.
- `04_fig1_by_model.csv` / `.png`: Figure 1 by model and temperature.
- `05_fig3_by_model.csv` / `.png`: Figure 3 by model and temperature.

Figures 1 and 2 pool initial choices across models and exclude skipped decisions. Figure 1 shades
each category by its frequency within a player's choices. Figure 2 uses plain bars.

To add an analysis, add a function `(rows, folder)` in `analyses.py`, return its
output paths, and register it in `handler.py`. Category mapping and round rows
live in `utils.py`; player filtering stays in the run script.
