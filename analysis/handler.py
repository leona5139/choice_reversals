"""Run selected analyses and save their CSV tables and figures."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from analysis.analyses import figure_1, figure_2, overview
from analysis.utils import round_rows, write_csv

ANALYSES = {0: overview, 1: figure_1, 2: figure_2}


def run_analysis(players, analysis_id, metadata=None, analysis_order=None):
    if not players:
        raise ValueError("no players selected; run a simulation or check the selection")
    order = list(analysis_order or ANALYSES)
    unknown = set(order) - ANALYSES.keys()
    if unknown:
        raise ValueError(f"unknown analysis IDs: {sorted(unknown)}")
    rows = round_rows(players)
    if not rows:
        raise ValueError("selected players have no saved rounds")
    folder = Path("output") / "analysis" / analysis_id
    folder.mkdir(parents=True, exist_ok=True)
    files = [write_csv(folder / "decisions.csv", rows)]
    for number in order:
        files += ANALYSES[number](rows, folder)
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    details = {
        **(metadata or {}),
        "analysis_id": analysis_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "analysis_order": order,
        "player_count": len(players),
        "player_ids": [p["player_id"] for p in players],
        "git_commit": commit,
        "files": [p.name for p in files],
    }
    (folder / "metadata.json").write_text(json.dumps(details, indent=2) + "\n")
    print(f"Saved analysis to {folder}")
    return folder
