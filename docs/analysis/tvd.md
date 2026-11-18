# Initial-choice TVD

Each cell compares one model setting with humans from the same treatment and rounds in Andreoni et al. (2020). Count each observed initial allocation once. In P, players choose only when their group wins. [Model data](../../output/results/milestone_2/players.jsonl) · [Human data](../../human_benchmark/processed/players.jsonl)

Total variation distance is half the sum of the absolute differences in the five choice-category shares. Zero means identical shares. One means no overlap. The report averages block TVDs with equal weight.

- **12 blocks.** Compare rounds 1–2, 3–4, and 5–8 within each treatment. [Heatmap](../../output/analysis/milestone_2/06_tvd_12_blocks.png) · [CSV](../../output/analysis/milestone_2/06_tvd_12_blocks.csv)
- **6 blocks.** Pool rounds 1–4 within `4A_4AR` and `4P_4AR` separately, then compare rounds 5–8 within each of the four treatments. [Heatmap](../../output/analysis/milestone_2/06_tvd_6_blocks.png) · [CSV](../../output/analysis/milestone_2/06_tvd_6_blocks.csv)
