"""Build human_benchmark/processed/players.jsonl from the original survey sessions.

Run with: uv run python -m analysis.process_human_benchmark
"""
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from simulation.run import new_rounds

RUN_NAME = "human_replication"
BENCHMARK = Path("human_benchmark")
RAW_SESSIONS = BENCHMARK / "raw" / "code and data files" / "data" / "de-identified"
PLAYERS = BENCHMARK / "processed" / "players.jsonl"
TREATMENTS = {"EA": "4A_4AR", "EP": "4P_4AR", "EAEP": "2A2P_4AR", "EPEA": "2P2A_4AR"}


def allocation(value):
    if value in ("", "NA"):
        return None
    b = int(value)  # The survey records tickets given to B.
    return {"A": 10 - b, "B": b}


def human_player(record, treatment, number):
    rounds = new_rounds(treatment)
    for n, rnd in rounds.items():
        slot = f"D{n}" if n <= 4 else str(n - 4)
        group = {"1": "computer", "2": "participant"}[record[f"flip{slot}"]]
        rnd["draw"] = {"group": group, "ticket": None}
        rnd["initial"] = allocation(record[f"choice{slot}"])
        if rnd["task"] == "AR":
            rnd["revision"] = allocation(record[f"choice{slot}r"])
        skipped = rnd["task"] == "P" and group == "computer"
        offered = rnd["task"] == "AR" and group == "participant"
        if (rnd["initial"] is None) != skipped or (rnd["revision"] is not None) != offered:
            raise ValueError(f"Unexpected decision for {record['ResponseID']} in round {n}")

    paid = int(record["round"])
    winner = record["winner"] or None
    rounds[paid]["winner"] = winner
    # ticketchosen is a payment field coded 1–10 for both groups, not a round-by-round ticket ID.
    payment = {"round": paid, "household": winner, "ticketchosen": int(record["ticketchosen"])}
    return {
        "player_id": record["ResponseID"], "run_name": RUN_NAME, "player_number": number,
        "provider": None, "model": "human", "temperature": None, "reasoning": None,
        "prompt_version": None, "treatment": treatment, "seed": None, "rounds": rounds,
        "payment": payment,
        "reversals": sum(r["revision"] is not None and r["initial"] != r["revision"] for r in rounds.values()),
        "cost": 0.0, "messages": [], "unsent": [],
    }


def read_sessions():
    players = []
    for code, treatment in TREATMENTS.items():
        number = 0
        for path in sorted(RAW_SESSIONS.glob(f"Fairness_v33Lot__{code}_EASR__*.csv")):
            with path.open(encoding="utf-8-sig", newline="") as file:
                for record in csv.DictReader(file):
                    if record["Finished"] in ("1", "True"):
                        players.append(human_player(record, treatment, number))
                        number += 1
    if len(players) != 239 or len({p["player_id"] for p in players}) != len(players):
        raise ValueError(f"Expected 239 distinct participants in the four main treatments under {RAW_SESSIONS}")
    return players


def main():
    players = read_sessions()
    PLAYERS.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=PLAYERS.parent) as tmp:
        staged = Path(tmp) / PLAYERS.name
        staged.write_text("".join(json.dumps(p) + "\n" for p in players), encoding="utf-8")
        staged.replace(PLAYERS)
    print(f"Saved {len(players)} human participants to {PLAYERS}")


if __name__ == "__main__":
    main()
