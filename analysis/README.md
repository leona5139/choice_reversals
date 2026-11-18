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
- `04_fig1_by_model` and `05_fig3_by_model` show Figures 1 and 3 for each model setting.
- `06_tvd_12_blocks` and `06_tvd_6_blocks` compare Milestone 2 initial choices with matched human choices. Each saves a heatmap and its counts. [TVD definition and block selection](../docs/analysis/tvd.md)
- `07_5_5_frames` compares the share choosing 5/5 in 4A and 4P in rounds 1–4. Each dot uses the observed initial choices in its treatment.
- `08_5_5_revisions` compares the same rounds before and after a revision offer, pooling rounds 5–8 across all four treatments. Its CSV also counts moves into and out of 5/5.

Charts 04–08 group by model, temperature, reasoning, prompt version, and run. The CSVs keep the prompt version. The charts label it only when the models use more than one version.

Figures 1 and 2 pool initial choices across models and exclude skipped decisions. Figure 1 shades
each category by its frequency within a player's choices. Figure 2 uses plain bars.

Add plots to `analyses.py` and register their IDs in `handler.py`. Each plot takes `(rows, folder)` and returns its output paths.
Keep shared calculations in `utils.py` and select players in the run script.

For the human figures, build `human_benchmark/processed/players.jsonl` once, then run the replication.

```sh
uv run python -m analysis.process_human_benchmark
uv run python -m analysis.run_analysis.human_replication
```
