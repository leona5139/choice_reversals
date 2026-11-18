"""Run with: uv run python -m analysis.run_analysis.human_replication"""
from pathlib import Path

from analysis.handler import run_analysis
from analysis.process_human_benchmark import PLAYERS, RAW_SESSIONS, load_human_players

ANALYSIS_IDS = [
    1,  # Figure 1. Initial choices in 4A and 4P
    2,  # Figure 2. Initial choices across treatments and round blocks
    3,  # Figure 3. Initial choices, revision offers, and changes across all four treatments
]
METADATA = {
    "selection": "Completed responses in the four main lottery treatments",
    "source": str(RAW_SESSIONS),
    "player_data": str(PLAYERS),
}


def main():
    if not PLAYERS.is_file():
        raise SystemExit(f"Missing {PLAYERS}. Run uv run python -m analysis.process_human_benchmark first.")
    players = load_human_players()
    run_analysis(players, Path(__file__).stem, METADATA, ANALYSIS_IDS)


if __name__ == "__main__":
    main()
