"""Run with: uv run python -m analysis.run_analysis.pilot_1"""
from pathlib import Path

from analysis.analyses import MAIN_TREATMENTS
from analysis.handler import run_analysis
from simulation.results import load_players

RUN_NAME = "pilot_1"
ANALYSIS_IDS = [
    0,  # Overview by treatment and task
    1,  # Figure 1. Initial choices in 4A and 4P, rounds 1–4
    2,  # Figure 2. Initial choices by treatment and round block
    3,  # Figure 3. Initial choices, eligible final choices, and changes across treatments, rounds 5–8
    4,  # Figure 1 by model setting, prompt version, and run
    5,  # Figure 3 by model setting, prompt version, and run
]
METADATA = {
    "title": "Pilot 1 analysis",
    "selection": f"All rounds from {RUN_NAME} for {', '.join(MAIN_TREATMENTS)}",
    "notes": "The original 60 players were collected under the run name test and retain their recorded seeds.",
}


def main():
    ## Load and filter players here.
    players = [p for p in load_players(RUN_NAME) if p.get("treatment") in MAIN_TREATMENTS]
    # Older saved players did not include run_name.
    players = [{**p, "run_name": p.get("run_name", RUN_NAME)} for p in players]
    if not players:
        raise SystemExit(f"No players from the four main treatments in output/results/{RUN_NAME}/players.jsonl.")
    run_analysis(players, Path(__file__).stem, METADATA, ANALYSIS_IDS)


if __name__ == "__main__":
    main()
