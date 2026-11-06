"""Checks the saved pilot replies against the counts reported in the Milestone 1 report.

Run from the repository folder, no extra packages needed:
    python analysis/check_pilot_replies.py            # defaults to pilot_1
    python analysis/check_pilot_replies.py pilot_1

Every assistant reply in players.jsonl is parsed the same way as simulation/parse.py
(the last {...} object) and compared with the decision stored for that question.
Replies that still deviate from the requested single-object format are counted.
The complete printed examples and their metadata are checked against the source.
Missing revisions, inconsistent records or example mismatches cause a nonzero exit.
"""
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

EVEN_SPLIT = {"A": 5, "B": 5}


def valid_allocation(data):
    return (isinstance(data, dict) and set(data) == {"A", "B"}
            and all(type(value) is int and 0 <= value <= 10 for value in data.values())
            and sum(data.values()) == 10)


def single_json_allocation(text):
    """A whole reply must be one valid object; JSON key order is irrelevant."""
    try:
        return valid_allocation(json.loads(text))
    except (json.JSONDecodeError, TypeError):
        return False


def parse_allocation(text):
    """Same rule as simulation/parse.py: the last JSON object in the reply."""
    objects = re.findall(r"\{[^{}]*\}", text or "")
    if not objects:
        return None
    try:
        data = json.loads(objects[-1])
    except json.JSONDecodeError:
        return None
    return data if valid_allocation(data) else None


def category(computer_a, participant_a):
    """The five choice categories of Andreoni et al. (2020)."""
    equalizing = 10 - computer_a
    if participant_a == equalizing:
        return "ex ante equalizing"
    if participant_a == 5:
        return "ex post equalizing"
    if (participant_a - equalizing) * (equalizing - 5) > 0:
        return "overcompensating"
    if min(equalizing, 5) < participant_a < max(equalizing, 5):
        return "mixed"
    return "reinforcing"


def load_players(run_name):
    path = os.path.join("output", "results", run_name, "players.jsonl")
    with open(path) as f:
        return [json.loads(line) for line in f]


def participant_number(player):
    """Earlier Gemini records keep the number only in their player ID."""
    number = int(player["player_id"].rsplit("|", 1)[-1])
    explicit = player.get("player_number", number)
    if type(explicit) is not int or explicit != number or number < 0:
        raise ValueError(f"invalid player number for {player['player_id']}")
    return number


def validate_players(players):
    if not players:
        raise ValueError("the saved run has no players")
    identifiers = [player["player_id"] for player in players]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate player IDs in the saved run")
    for player in players:
        for key in ("model", "treatment", "prompt_version"):
            if not isinstance(player[key], str) or not player[key]:
                raise ValueError(f"invalid {key} for {player['player_id']}")
        number = participant_number(player)
        expected_id = (f"{player['treatment']}|{player['model']}|t={player['temperature']}|"
                       f"{player['prompt_version']}|{number}")
        if player["player_id"] != expected_id:
            raise ValueError(f"player metadata differs from its ID: {player['player_id']}")
        for key, this_round in player["rounds"].items():
            if str(this_round["round"]) != key:
                raise ValueError(f"round key differs from its number for {player['player_id']}")
            eligible = (this_round["task"] == "AR"
                        and this_round["draw"]["group"] == "participant")
            if eligible and not valid_allocation(this_round["revision"]):
                raise ValueError(f"missing or invalid eligible revision for {player['player_id']}, round {key}")


def check_replies(players):
    """Every reply must parse to the stored decision for its question."""
    replies = fenced = repeated = other = mismatches = 0
    deviations = Counter()
    for player in players:
        messages = player["messages"]
        for index, message in enumerate(messages):
            if message["role"] != "assistant":
                continue
            replies += 1
            if index == 0 or messages[index - 1]["role"] != "user":
                raise ValueError(f"reply has no preceding question for {player['player_id']}, message {index}")
            question = messages[index - 1]["content"]
            match = re.search(r"Round (\d+)", question)
            if not match:
                raise ValueError(f"question has no round number for {player['player_id']}, message {index - 1}")
            round_number = match.group(1)
            field = "revision" if question.startswith("Earlier in Round") else "initial"
            parsed = parse_allocation(message["content"])
            if parsed is None or parsed != player["rounds"][round_number][field]:
                mismatches += 1
            text = message["content"]
            if single_json_allocation(text):
                continue
            deviations[player["model"]] += 1
            if "```" in text:
                fenced += 1
            elif len(re.findall(r"\{[^{}]*\}", text)) > 1:
                repeated += 1
            else:
                other += 1
    print(f"replies: {replies}, format deviations: {sum(deviations.values())} "
          f"(code fences {fenced}, repeated objects {repeated}, other {other})")
    for model, count in sorted(deviations.items()):
        print(f"  {model}: {count}")
    print(f"replies whose parsed allocation differs from the stored decision: {mismatches}")
    if mismatches:
        raise ValueError(f"{mismatches} replies fail to reproduce their saved decisions")


def initial_choices(players, treatment):
    """Rounds 1-4 of one treatment: category counts overall and by model."""
    overall, by_model = Counter(), {}
    for player in players:
        if player["treatment"] != treatment:
            continue
        for this_round in player["rounds"].values():
            if this_round["round"] > 4 or this_round["initial"] is None:
                continue
            name = category(this_round["computer"]["A"], this_round["initial"]["A"])
            overall[name] += 1
            by_model.setdefault(player["model"], Counter())[name] += 1
    print(f"{treatment} rounds 1-4: {sum(overall.values())} choices, {dict(overall)}")
    for model, counts in sorted(by_model.items()):
        print(f"  {model}: {sum(counts.values())} choices, {dict(counts)}")


def revisions(players):
    """Eligible AR rounds (participant win) and how many choices changed."""
    total = Counter()
    for player in players:
        for this_round in player["rounds"].values():
            if this_round["task"] != "AR" or this_round["draw"]["group"] != "participant":
                continue
            key = (player["treatment"], player["model"])
            total[key, "eligible"] += 1
            if this_round["revision"] != this_round["initial"]:
                total[key, "changed"] += 1
                if this_round["revision"] == EVEN_SPLIT:
                    total[key, "to 5/5"] += 1
    treatments = sorted({key[0] for key, _ in total})
    for treatment in treatments:
        eligible = sum(n for (key, what), n in total.items() if key[0] == treatment and what == "eligible")
        changed = sum(n for (key, what), n in total.items() if key[0] == treatment and what == "changed")
        print(f"{treatment}: {changed} of {eligible} eligible choices changed")
        for model in sorted({key[1] for key, _ in total if key[0] == treatment}):
            key = (treatment, model)
            print(f"  {model}: changed {total[key, 'changed']} of {total[key, 'eligible']}, "
                  f"to 5/5 {total[key, 'to 5/5']}")
    print(f"all treatments: {sum(n for (_, what), n in total.items() if what == 'changed')} of "
          f"{sum(n for (_, what), n in total.items() if what == 'eligible')} eligible choices changed")
    for model in sorted({key[1] for key, _ in total}):
        counts = {what: sum(n for (key, kind), n in total.items()
                            if key[1] == model and kind == what)
                  for what in ("eligible", "changed", "to 5/5")}
        print(f"  {model} across all treatments: changed {counts['changed']} of "
              f"{counts['eligible']}, to 5/5 {counts['to 5/5']}")


def eligible_final_choices(players, treatment):
    """Final choices in the eligible AR rounds only, as in the human final panel."""
    initial, final, already_even = Counter(), Counter(), 0
    for player in players:
        if player["treatment"] != treatment:
            continue
        for this_round in player["rounds"].values():
            if this_round["task"] != "AR" or this_round["draw"]["group"] != "participant":
                continue
            computer_a = this_round["computer"]["A"]
            initial[category(computer_a, this_round["initial"]["A"])] += 1
            last = this_round["revision"] or this_round["initial"]
            final[category(computer_a, last["A"])] += 1
            if this_round["initial"] == EVEN_SPLIT and last == EVEN_SPLIT:
                already_even += 1
    print(f"{treatment} eligible rounds: {sum(final.values())}; initial {dict(initial)}; "
          f"final {dict(final)}; final 5/5 that were already 5/5: {already_even}")


def check_examples(players):
    """Compare each complete printed example and its metadata with saved messages."""
    path = Path("docs/assets/pilot-response-examples.txt")
    sections = re.split(r"(?m)^\[EXAMPLE \d+\]\n", path.read_text(encoding="utf-8"))[1:]
    if not sections:
        raise ValueError(f"no examples found in {path}")
    for number, section in enumerate(sections, 1):
        metadata, content = section.split("\n[PROMPT]\n", 1)
        prompt, reply = content.split("\n\n[RAW REPLY]\n", 1)

        def value(label):
            match = re.search(rf"(?m)^{re.escape(label)} (.+)$", metadata)
            if not match:
                raise ValueError(f"example {number} has no {label}")
            return match.group(1)

        line = int(value("JSONL line"))
        prompt_index = int(value("Prompt message index"))
        reply_index = int(value("Reply message index"))
        if not 1 <= line <= len(players) or min(prompt_index, reply_index) < 0:
            raise ValueError(f"example {number} has an invalid source index")
        player = players[line - 1]
        source_prompt = player["messages"][prompt_index]
        source_reply = player["messages"][reply_index]
        round_match = re.search(r"Round (\d+)", source_prompt["content"])
        expected_metadata = (player["model"], player["treatment"],
                             str(participant_number(player)), round_match.group(1) if round_match else None)
        shown_metadata = tuple(value(key) for key in ("Model", "Condition", "Participant number", "Round"))
        if shown_metadata != expected_metadata:
            raise ValueError(f"example {number} metadata differs from its source")
        if (reply_index != prompt_index + 1 or source_prompt["role"] != "user"
                or source_reply["role"] != "assistant"
                or prompt != source_prompt["content"]
                or reply.rstrip("\n") != source_reply["content"].rstrip("\n")):
            raise ValueError(f"example {number} text differs from its source")
        print(f"example {number}: complete prompt, reply and metadata match line {line}")


def main(run_name):
    players = load_players(run_name)
    validate_players(players)
    setups = Counter((p["model"], p["treatment"]) for p in players)
    print(f"players: {len(players)} in {len({p['model'] for p in players})} models x "
          f"{len({p['treatment'] for p in players})} treatments, "
          f"{min(setups.values())}-{max(setups.values())} per model and treatment")
    print(f"temperatures: {sorted({p['temperature'] for p in players})}, "
          f"prompt versions: {sorted({p['prompt_version'] for p in players})}")
    check_replies(players)
    initial_choices(players, "4A_4AR")
    initial_choices(players, "4P_4AR")
    revisions(players)
    eligible_final_choices(players, "4A_4AR")
    print("report examples (Appendix C):")
    check_examples(players)


if __name__ == "__main__":
    try:
        main(sys.argv[1] if len(sys.argv) > 1 else "pilot_1")
    except (ValueError, KeyError, IndexError, TypeError, OSError) as error:
        print(f"CHECK FAILED: {error}", file=sys.stderr)
        sys.exit(1)
