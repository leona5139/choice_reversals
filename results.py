"""Each run is saved to results/<run_name>/:
    players.jsonl              one finished player per line
    requests.jsonl             every API attempt, including invalid replies
    outline_<treatment>.json   the outline each treatment followed
"""
import json
import os
import threading

EVEN_SPLIT = {"A": 5, "B": 5}

file_lock = threading.Lock()


def append_jsonl(path, record):
    with file_lock:
        with open(path, "a") as f:
            f.write(json.dumps(record) + "\n")


def load_players(run_name):
    path = os.path.join("results", run_name, "players.jsonl")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f]


def is_ex_ante_equalizing(this_round):
    return this_round["initial"]["A"] == 10 - this_round["computer"]["A"]


def group_by_setup(players):
    groups = {}
    for player in players:
        key = (player["treatment"], player["model"], player["temperature"])
        groups.setdefault(key, []).append(player)
    return groups


def print_revisions(rounds):
    offered = [r for r in rounds if r["revision"]]
    revised = [r for r in offered if r["revision"] != r["initial"]]
    revised_to_even = [r for r in revised if r["revision"] == EVEN_SPLIT]
    print(f"    revised {len(revised)} of {len(offered)} choices; {len(revised_to_even)} of those to 5/5")


def print_initial_choices(rounds, task):
    chosen = [r for r in rounds if r["task"] == task and r["initial"]]
    if not chosen:
        return
    ex_ante = [r for r in chosen if is_ex_ante_equalizing(r)]
    even = [r for r in chosen if r["initial"] == EVEN_SPLIT]
    print(f"    initial {task:<2}: {len(ex_ante)} of {len(chosen)} ex ante equalizing, {len(even)} at 5/5")


def print_summary(run_name):
    groups = group_by_setup(load_players(run_name))

    for (treatment, model, temperature), players in sorted(groups.items()):
        rounds = [this_round for player in players for this_round in player["rounds"].values()]
        cost = sum(player["cost"] for player in players)

        print(f"{treatment} | {model} | t={temperature} | {len(players)} players | ${cost:.4f}")
        print_revisions(rounds)
        for task in ["A", "P", "AR"]:
            print_initial_choices(rounds, task)
