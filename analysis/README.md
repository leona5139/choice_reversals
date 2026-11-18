# Analysis

Set `ANALYSIS_IDS` in the run script to choose which analyses to run.
For example, `[1, 3]` selects Figures 1 and 3. An empty list selects all available IDs.

From the repository folder:

```sh
uv run python -m analysis.run_analysis.pilot_1
```

Each run writes its outputs to `output/analysis/<run script name>/`.

- `metadata.json`: notes, timestamp, selected players, and files updated this run.
- `decisions.csv`: every player's rounds, allocations, and choice categories.
- `00_overview.csv`: counts by model setup, treatment, and task.
- `01_fig1_choices.csv` / `.png`: pure A/P treatments, rounds 1–4.
- `02_fig2_choices.csv` / `.png`: all treatments, rounds 1–2, 3–4, and 5–8.
- `03_fig3_revisions.csv` / `.png` pool rounds 5–8 of all four treatments. The panels show all initial choices, responses to revision offers (including keeps), and changed allocations. Both revision panels measure consistency over each player’s full set of responses to offers.
- `04_fig1_by_model` and `05_fig3_by_model` each save a CSV and PNG grouped by model, temperature, reasoning, prompt version, and run name when available.

Figures 1 and 2 pool initial choices across models and exclude skipped decisions. Figure 1 shades
each category by its frequency within a player's choices. Figure 2 uses plain bars.

To add an analysis, add a function `(rows, folder)` in `analyses.py`, return its
output paths, and register it in `handler.py`. Category mapping and round rows
live in `utils.py`; player filtering stays in the run script.

For the human figures, build `human_benchmark/processed/players.jsonl` once, then run the replication.

```sh
uv run python -m analysis.process_human_benchmark
uv run python -m analysis.run_analysis.human_replication
```
