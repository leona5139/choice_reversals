"""Run with: uv run python -m analysis.run_analysis.milestone_2"""

from pathlib import Path

from analysis.handler import run_analysis
from simulation.results import load_players

RUN_NAME = "milestone_2"
ANALYSIS_IDS = [
    0,  # Overview by treatment and task
    1,  # Figure 1. Initial choices in 4A and 4P, rounds 1–4
    2,  # Figure 2. Initial choices by treatment and round block
    3,  # Figure 3. Initial choices, eligible final choices, and changes across treatments, rounds 5–8
    4,  # Figure 1 by model setting, prompt version, and run
    5,  # Figure 3 by model setting, prompt version, and run
    6,  # Initial-choice TVD against humans, with 12-block and 6-block heatmaps
    7,  # Share choosing 5/5 in 4A and 4P, rounds 1–4
    8,  # Share choosing 5/5 before and after a revision offer, rounds 5–8
]

METADATA = {
    "title": "Milestone 2 analysis",
    "selection": "All players and rounds from milestone 2",
    "notes": "",
}


def main():
    ## Load and filter players here.
    players = load_players(RUN_NAME)
    # Older saved players did not include run_name.
    players = [{**p, "run_name": p.get("run_name", RUN_NAME)} for p in players]
    if not players:
        raise SystemExit(
            f"No players in output/results/{RUN_NAME}/players.jsonl. Run the simulation first."
        )
    run_analysis(players, Path(__file__).stem, METADATA, ANALYSIS_IDS)


if __name__ == "__main__":
    main()
