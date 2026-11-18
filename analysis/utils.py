"""Round records and choice statistics."""
from collections import Counter
import csv

SETUP_FIELDS = ("provider", "model", "temperature", "reasoning", "prompt_version")
MODEL_FIELDS = ("model", "temperature", "reasoning", "prompt_version", "run_name")
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
            row["reasoning"] = player.get("reasoning", "default")
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
        key = tuple((row.get(field) or None) if field in ("prompt_version", "run_name") else row[field]
                    for field in fields)
        groups.setdefault(key, []).append(row)
    return dict(sorted(groups.items(), key=lambda item: tuple(str(v) for v in item[0])))


def marginal_distribution(rows, category_field, *, changes_only=False, with_consistency=True):
    """For changes, measure each player's consistency across all eligible responses."""
    per_player = {}
    for row in rows:
        category = row[category_field]
        if category is not None:
            per_player.setdefault(player_key(row), Counter())[category] += 1
    if changes_only:
        rows = [r for r in rows if r["changed"] is True]
    choices = [r for r in rows if r[category_field] is not None]
    counts = Counter()
    for row in choices:
        category = row[category_field]
        own = per_player[player_key(row)]
        level = own[category] / own.total() if with_consistency else None
        counts[category, level] += 1
    levels = sorted({level for _, level in counts}) or [None]
    n_players = len({player_key(r) for r in rows})
    n_respondents = len({player_key(r) for r in choices})
    table = []
    for category in CATEGORIES:
        for consistency in levels:
            count = counts[category, consistency]
            table.append({
                "category": category,
                "consistency": consistency,
                "count": count,
                "percent": 100 * count / len(choices) if choices else None,
                "n_players": n_players,
                "n_respondents": n_respondents,
                "n_choices": len(choices),
            })
    return table


def choice_distribution(rows, with_consistency=False, by=()):
    fields = (*by, "treatment", "period")
    table = []
    for key, group in group_rows(rows, fields).items():
        labels = dict(zip(fields, key))
        distribution = marginal_distribution(group, "initial_category", with_consistency=with_consistency)
        table.extend({**labels, **record} for record in distribution)
    return table


def total_variation(model, human):
    n_model, n_human = model.total(), human.total()
    if not n_model or not n_human:
        return None
    return 0.5 * sum(abs(model[c] / n_model - human[c] / n_human) for c in CATEGORIES)


def equal_split_summary(setup, first, second):
    result = dict(zip(MODEL_FIELDS, setup))
    for prefix, (stage, choices) in (("first", first), ("second", second)):
        even = choices.count(5)
        result[f"{prefix}_stage"] = stage
        result[f"{prefix}_choices"] = len(choices)
        result[f"{prefix}_5_5"] = even
        result[f"{prefix}_percent"] = 100 * even / len(choices) if choices else None
    a, b = result["first_percent"], result["second_percent"]
    result["change_pp"] = b - a if a is not None and b is not None else None
    return result


def write_csv(path, rows, fields=None):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
