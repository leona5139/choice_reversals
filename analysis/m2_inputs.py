"""Comparable human and model rounds for the four main lottery conditions.

load_samples returns one dictionary per scheduled round, including skipped P
rounds (initial_a=None). final_a is the post-reveal allocation for an actual
revision offer, including keeping the initial choice. It is None elsewhere.
All ticket counts use household A.
"""

import csv
import io
import json
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from analysis.utils import classify_allocation, round_rows
from simulation.game import COMPUTER_TICKETS_TO_A
from simulation.treatments import TREATMENTS, tasks_in

# These are the four lottery treatments listed in the authors' data-cleaning.R.
SESSION_CODES = {
    "EA_EASR": "4A_4AR",
    "EP_EASR": "4P_4AR",
    "EAEP_EASR": "2A2P_4AR",
    "EPEA_EASR": "2P2A_4AR",
}
# OffsettingAmount in the authors' data-cleaning.R is the human B allocation
# that offsets the computer, numerically equal to the computer's tickets to A.
HUMAN_COMPUTER_TICKETS_TO_A = (7, 2, 10, 1, 8, 3, 9, 0)


def _tickets_to_a(value):
    # The human survey records tickets to B. A receives the other tickets.
    return None if value in ("", "NA") else 10 - int(value)


def _human_rounds(path):
    rows = []
    session_path = PurePosixPath("code and data files/data/de-identified")
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            path_in_zip = PurePosixPath(name)
            parts = path_in_zip.stem.split("__")
            if (path_in_zip.parent != session_path or path_in_zip.suffix != ".csv"
                    or len(parts) < 2 or parts[0] != "Fairness_v33Lot" or parts[1] not in SESSION_CODES):
                continue
            treatment = SESSION_CODES[parts[1]]
            with archive.open(name) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as source:
                for record in csv.DictReader(source):
                    if record["Finished"] not in ("1", "True"):
                        continue
                    for number, task in enumerate(tasks_in(treatment), 1):
                        # D1-D4 identify rounds 1-4; 1-4 identify rounds 5-8.
                        suffix = f"D{number}" if number <= 4 else str(number - 4)
                        draw_group = {"1": "computer", "2": "participant"}[record[f"flip{suffix}"]]
                        initial = _tickets_to_a(record[f"choice{suffix}"])
                        final = _tickets_to_a(record[f"choice{suffix}r"]) if task == "AR" else None
                        computer = HUMAN_COMPUTER_TICKETS_TO_A[number - 1]
                        rows.append({
                            "player_id": record["ResponseID"], "treatment": treatment,
                            "round": number, "task": task, "draw_group": draw_group,
                            "computer_a": computer, "initial_a": initial,
                            "initial_category": classify_allocation(computer, initial),
                            "final_a": final, "revision_offered": task == "AR" and draw_group == "participant",
                            "changed": final != initial if final is not None else None,
                        })
    return rows


def _validate_rounds(label, rows):
    players = {}
    offers = Counter()
    for row in rows:
        player = row["player_id"]
        treatment = row["treatment"]
        number = row["round"]
        if treatment not in TREATMENTS or not 1 <= number <= 8:
            raise ValueError(f"{label}, {player}: unexpected treatment or round")
        treatment_seen, rounds = players.setdefault(player, (treatment, set()))
        if treatment != treatment_seen or number in rounds:
            raise ValueError(f"{label}, {player}: repeated round or treatment mismatch")
        rounds.add(number)
        if (row["task"] != tasks_in(treatment)[number - 1]
                or row["computer_a"] != COMPUTER_TICKETS_TO_A[number - 1]
                or row["draw_group"] not in ("computer", "participant")):
            raise ValueError(f"{label}, {player}, round {number}: unexpected lottery design")
        observed = row["task"] != "P" or row["draw_group"] == "participant"
        offered = row["task"] == "AR" and row["draw_group"] == "participant"
        if (row["initial_a"] is not None) != observed or (row["final_a"] is not None) != offered:
            raise ValueError(f"{label}, {player}, round {number}: observed choice or revision disagrees with draw")
        if offered and not 0 <= row["final_a"] <= 10:
            raise ValueError(f"{label}, {player}, round {number}: invalid revised allocation")
        offers[player] += offered
    if not players or any(len(rounds) != 8 for _, rounds in players.values()):
        raise ValueError(f"{label}: missing participant rounds")
    if any(count != 2 for count in offers.values()):
        raise ValueError(f"{label}: expected two revision offers per participant")
    if {treatment for treatment, _ in players.values()} != set(TREATMENTS):
        raise ValueError(f"{label}: one or more main treatments are missing")


def load_samples(root: Path):
    """Load original human sessions and saved M2 runs without any API calls.

    Model keys include the full model identifier and the requested reasoning
    setting. The earlier Gemma default runs have their own key. The sample name
    assumes the M2 provider, prompt version and temperature used in this dataset.
    """
    root = Path(root)
    samples = {"Human": _human_rounds(root / "human_benchmark/raw/2016200data.zip")}
    players_path = root / "output/results/milestone_2/players.jsonl"
    with players_path.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            player = json.loads(line)
            if (player["provider"], player["temperature"], player["prompt_version"]) != ("openrouter", 1, "prompt_a"):
                raise ValueError("Separate provider, temperature or prompt version before comparing these records")
            label = f"{player['model']} [{player.get('reasoning', 'default')}]"
            rows = samples.setdefault(label, [])
            for row in round_rows([player]):
                observation = {key: row[key] for key in (
                    "player_id", "treatment", "round", "task", "draw_group",
                    "computer_a", "initial_a", "initial_category", "revision_offered", "changed",
                )}
                observation["final_a"] = row["revision_a"]
                rows.append(observation)
    for setting, rows in samples.items():
        _validate_rounds(setting, rows)
    return samples
