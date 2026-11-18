# Analysis

## Milestone 2 human comparison

From the repository root, run the following command with Python 3.11 or newer and Matplotlib installed.

```sh
python -m analysis.compare_m2
```

This analysis runs offline. It reads `output/results/milestone_2/players.jsonl` and the authors' ten relevant sessions in `human_benchmark/raw/2016200data.zip`. The [working report and API setup](../docs/writeups/milestone2_draft.pdf) use the following outputs in [m2_comparison](../output/analysis/m2_comparison/).

Run `python -m analysis.replay_m2` to replay the four archived schedules and all accepted replies. It checks conversation text, unsent messages, lottery outcomes, payment selections and revision counts against the saved records, and counts departures from the requested reply format.

- `initial_choices.csv` gives counts and shares in the paper's five categories. Each setting is compared with humans within the same condition and rounds. The six equally weighted blocks cover the first four rounds of 4A and 4P and the last four rounds of each condition.
- `framing.csv` gives the frequency of a 5/5 split among observed choices by the independent 4A and 4P groups in rounds 1–4. In P rounds a person or model allocates tickets only when the participant's group wins.
- `revisions.csv` follows every eligible decision before and after the reveal. The summary averages rates equally across the four conditions. Its count fields are totals. A blank share of changes ending at 5/5 means its denominator was zero in at least one contributing condition.
- `tvd.png` and `framing_and_revisions.png` show the same comparisons for all settings. The earlier 40 Gemma runs had no explicit reasoning request and are labelled separately from the 11 planned settings.

### Findings for the three comparisons

**Point 1. Initial allocations.** The six-block mean TVD was lowest for DeepSeek with high reasoning (0.315) and highest for Haiku with reasoning off (0.815). Within the latter setting, its early 4P choices were closer to humans (TVD 0.42) than its early 4A choices (0.92). The six-block option compares the two pure conditions before participants have changed frames, then compares all four conditions when the revision procedure is the same.

**Point 2. Initial 5/5 splits in 4A and 4P.** In the first four rounds, humans split the tickets equally on 23 of 284 choices in 4A (8.1%) and 62 of 144 in 4P (43.1%). The 35.0 percentage point difference compares two groups of people. Eight of the 11 planned model settings also chose 5/5 more often in 4P. Both Haiku settings chose it less often in 4P, and Gemma with reasoning off chose it in neither group.

**Point 3. Revisions after the reveal.** There were 478 human decisions with a revision opportunity. Giving each of the four conditions equal weight, the human 5/5 rate rose from 7.1% before the reveal to 56.4% afterward. Eight of 11 model settings also showed an increase. DeepSeek with high reasoning went from 0% to 87.5%, while Haiku with reasoning off kept its initial allocation on all 160 offers. Looking at changes to any allocation across the four conditions, humans changed 315 choices, of which 243 ended at 5/5. The pooled revision rate was 315/478 (65.9%). Giving each condition equal weight yields the 65.2% shown in the report. Six of the 11 main settings showed both human directions, more 5/5 choices in 4P than in 4A and more 5/5 choices after the reveal.

## Existing simulation plots

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
