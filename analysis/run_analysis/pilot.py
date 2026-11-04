"""Run with: uv run python -m analysis.run_analysis.pilot"""
from pathlib import Path

from analysis.handler import run_analysis
from results import load_players

RUN_NAME = "pilot_1"
ANALYSIS_ORDER = []  # All analyses; use [0, 1] for the overview and Figure 1.
METADATA = {
    "title": "Pilot analysis",
    "selection": "All players and rounds from pilot_1",
    "notes": "",
}


def main():
    ## Load and filter players here.
    players = load_players(RUN_NAME)
    # Older saved players did not include run_name.
    players = [{**p, "run_name": p.get("run_name", RUN_NAME)} for p in players]
    if not players:
        raise SystemExit(f"No players in results/{RUN_NAME}/players.jsonl. Run the simulation first.")
    run_analysis(players, Path(__file__).stem, METADATA, ANALYSIS_ORDER)


if __name__ == "__main__":
    main()
