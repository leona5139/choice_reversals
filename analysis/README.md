# Analysis

Edit `run_analysis/pilot.py` to select players from `pilot_1`, add notes, or set
`ANALYSIS_ORDER`: `[]` runs all; `[2, 1]` runs Figure 2 then Figure 1.

From the repository folder:

```sh
uv run python -m analysis.run_analysis.pilot
```

Selected outputs in `output/analysis/pilot/` are overwritten on rerun:

- `metadata.json`: notes, timestamp, selected players, and files updated this run.
- `decisions.csv`: every player's rounds, allocations, and choice categories.
- `00_overview.csv`: counts by model setup, treatment, and task.
- `01_fig1_choices.csv` / `.png`: pure A/P treatments, rounds 1–4.
- `02_fig2_choices.csv` / `.png`: all treatments, rounds 1–2, 3–4, and 5–8.

Both figures use initial choices; skipped decisions are excluded. Figure 1 shades
each category by its frequency within a player's choices. Figure 2 uses plain bars.
Models, providers, temperatures, and prompt versions stay separate.

To add an analysis, add a function `(rows, folder)` in `analyses.py`, return its
output paths, and register it in `handler.py`. Category mapping and round rows
live in `utils.py`; player filtering stays in the run script.
