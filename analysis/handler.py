"""Run selected analyses and save their CSV tables and figures."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from analysis import analyses
from analysis.utils import round_rows, write_csv

ANALYSES = {
    0: analyses.overview,
    1: analyses.figure_1,
    2: analyses.figure_2,
    3: analyses.figure_3,
    4: analyses.figure_1_by_model,
    5: analyses.figure_3_by_model,
    6: analyses.initial_choice_tvd,
    7: analyses.equal_split_frames,
    8: analyses.equal_split_revisions,
}


def run_analysis(players, analysis_id, metadata=None, analysis_ids=None):
    if not players:
        raise ValueError("no players selected; run a simulation or check the selection")
    selected_ids = list(analysis_ids or ANALYSES)
    unknown = set(selected_ids) - ANALYSES.keys()
    if unknown:
        raise ValueError(f"unknown analysis IDs: {sorted(unknown)}")
    rows = round_rows(players)
    if not rows:
        raise ValueError("selected players have no saved rounds")
    folder = Path("output") / "analysis" / analysis_id
    folder.mkdir(parents=True, exist_ok=True)
    files = [write_csv(folder / "decisions.csv", rows)]
    for number in selected_ids:
        files += ANALYSES[number](rows, folder)
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    details = {
        **(metadata or {}),
        "analysis_id": analysis_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "analysis_ids": selected_ids,
        "player_count": len(players),
        "round_count": len(rows),
        "player_ids": [p["player_id"] for p in players],
        "git_commit": commit,
        "files": [p.name for p in files],
    }
    (folder / "metadata.json").write_text(json.dumps(details, indent=2) + "\n")
    print(f"Saved analysis to {folder}")
    return folder
