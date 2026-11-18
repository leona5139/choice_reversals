"""Builds a treatment's outline: the order in which the prompt slots are used.

Print an outline with `uv run python -m simulation.treatments 2A2P_4AR`.
"""
import json
import re
import sys
from pathlib import Path

SHOW_OUTCOMES = True


def tasks_in(treatment):
    """"2A2P_4AR" -> ["A", "A", "P", "P", "AR", "AR", "AR", "AR"]"""
    tasks = []
    for count, task in re.findall(r"(\d+)(AR|A|P)", treatment):
        tasks += [task] * int(count)

    if not tasks:
        raise ValueError(f"cannot read treatment {treatment!r}")
    return tasks


def load_instances():
    """Read the four main conditions and the Table 3 computer allocations."""
    path = Path(__file__).with_name("instances.json")
    with path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    names = data["treatments"]
    tickets = data["computer_tickets_to_a"]
    if len(tickets) != 8 or any(type(n) is not int or not 0 <= n <= 10 for n in tickets):
        raise ValueError(f"{path}: expected eight integer allocations of 0 to 10 tickets")
    if not names or len(names) != len(set(names)):
        raise ValueError(f"{path}: treatment names must be present and unique")
    for name in names:
        if not re.fullmatch(r"(?:[1-9]\d*(?:A|P))+_[1-9]\d*AR", name) or len(tasks_in(name)) != len(tickets):
            raise ValueError(f"{path}: invalid eight-round treatment {name!r}")
    return names, tickets


TREATMENTS, COMPUTER_TICKETS_TO_A = load_instances()


def step(kind, round_number=None, slot=None, only_if_winner=None):
    name = slot.lower() if slot else kind
    step_id = f"r{round_number}_{name}" if round_number else name
    return {"id": step_id, "kind": kind, "round": round_number, "slot": slot, "only_if_winner": only_if_winner}


def outcome_steps(round_number, slot):
    """OUTCOME_A (A and AR rounds) hides the winning ticket; OUTCOME_P (P rounds) reveals it."""
    if SHOW_OUTCOMES:
        return [step("message", round_number, slot)]
    return []


def ex_ante_round(round_number):
    return [
        step("ask", round_number, "ALLOCATION"),
        step("draw", round_number),
        step("resolve", round_number),
    ] + outcome_steps(round_number, "OUTCOME_A")


def ex_post_round(round_number):
    return [
        step("draw", round_number),
        step("message", round_number, "GROUP_REVEAL"),
        step("ask", round_number, "ALLOCATION", only_if_winner="participant"),
        step("resolve", round_number),
    ] + outcome_steps(round_number, "OUTCOME_P")


def surprise_revision_rounds(round_numbers):
    every_allocation_first = [step("ask", round_number, "ALLOCATION") for round_number in round_numbers]

    reveals_and_revisions = []
    for round_number in round_numbers:
        reveals_and_revisions += [
            step("draw", round_number),
            step("message", round_number, "GROUP_REVEAL"),
            step("ask", round_number, "REVISION", only_if_winner="participant"),
            step("resolve", round_number),
        ] + outcome_steps(round_number, "OUTCOME_A")

    return every_allocation_first + reveals_and_revisions


def build_outline(treatment):
    tasks = tasks_in(treatment)
    revision_rounds = [round_number for round_number, task in enumerate(tasks, start=1) if task == "AR"]
    outline = [step("message", slot="INSTRUCTIONS")]

    for round_number, task in enumerate(tasks, start=1):
        if task == "A":
            outline += ex_ante_round(round_number)
        elif task == "P":
            outline += ex_post_round(round_number)
        elif round_number == revision_rounds[0]:
            outline += surprise_revision_rounds(revision_rounds)

    outline.append(step("payment"))
    return outline


def describe(outline):
    lines = []
    for each_step in outline:
        line = f"{each_step['id']:<20}{each_step['kind']:<9}{each_step['slot'] or ''}"
        if each_step["only_if_winner"]:
            line += f"   (only if {each_step['only_if_winner']} group won)"
        lines.append(line)
    return "\n".join(lines)


if __name__ == "__main__":
    for treatment in sys.argv[1:] or TREATMENTS:
        print(f"=== {treatment} ===")
        print(describe(build_outline(treatment)))
        print()
