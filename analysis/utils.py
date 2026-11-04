"""Shared choice categories and one-row-per-player-round data."""
import csv

SETUP_FIELDS = ("provider", "model", "temperature", "prompt_version")
PLAYER_FIELDS = ("run_name", "player_id", "player_number", "treatment", *SETUP_FIELDS)
CATEGORIES = (
    "overcompensating", "ex_ante_equalizing", "mixed",
    "ex_post_equalizing", "reinforcing",
)


def classify_allocation(computer_a, participant_a):
    if participant_a is None:
        return None
    if any(type(n) is not int or not 0 <= n <= 10 for n in (computer_a, participant_a)):
        raise ValueError("ticket counts must be integers from 0 to 10")
    if computer_a == 5:
        raise ValueError("the paper's five categories require an unequal computer allocation")
    equalizing = 10 - computer_a
    if participant_a == equalizing:
        return "ex_ante_equalizing"
    if participant_a == 5:
        return "ex_post_equalizing"
    if (participant_a - equalizing) * (equalizing - 5) > 0:
        return "overcompensating"
    if min(equalizing, 5) < participant_a < max(equalizing, 5):
        return "mixed"
    return "reinforcing"


def player_key(record):
    return record.get("run_name"), record["player_id"]


def round_rows(players):
    rows = []
    for player in players:
        for this_round in sorted(player["rounds"].values(), key=lambda r: r["round"]):
            initial = this_round["initial"]
            revision = this_round["revision"]
            draw = this_round["draw"] or {}
            number = this_round["round"]
            row = {field: player.get(field) for field in PLAYER_FIELDS}
            row.update({
                "seed": player["seed"],
                "round": number,
                "period": "1-2" if number <= 2 else "3-4" if number <= 4 else "5-8",
                "task": this_round["task"],
                "computer_a": this_round["computer"]["A"],
                "computer_b": this_round["computer"]["B"],
                "draw_group": draw.get("group"),
                "ticket": draw.get("ticket"),
                "winner": this_round["winner"],
                "revision_offered": this_round["task"] == "AR" and draw.get("group") == "participant",
                "changed": revision != initial if revision is not None else None,
            })
            for name, allocation in (("initial", initial), ("revision", revision), ("final", revision or initial)):
                allocation = allocation or {}
                row[f"{name}_a"] = allocation.get("A")
                row[f"{name}_b"] = allocation.get("B")
                row[f"{name}_category"] = classify_allocation(row["computer_a"], allocation.get("A"))
            rows.append(row)
    return rows


def group_rows(rows, fields):
    groups = {}
    for row in rows:
        key = tuple(row[field] for field in fields)
        groups.setdefault(key, []).append(row)
    return dict(sorted(groups.items(), key=lambda item: tuple(str(v) for v in item[0])))


def write_csv(path, rows, fields=None):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
