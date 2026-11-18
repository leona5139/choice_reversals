"""Replay the saved Milestone 2 conversations without sending API requests."""

import json
from pathlib import Path

from analysis.check_pilot_replies import single_json_allocation
from prompt import prompt_a
from simulation.parse import parse_allocation
from simulation.run import player_seed, run_player
from simulation.treatments import TREATMENTS, build_outline

DATA = Path(__file__).resolve().parents[1] / "output/results/milestone_2"


def replay(record):
    player = record["player_id"]
    replies = iter(message["content"] for message in record["messages"] if message["role"] == "assistant")
    count = departures = 0

    def answer(messages):
        nonlocal count, departures
        text = next(replies, None)
        if text is None:
            raise ValueError(f"{player}: transcript ended before the next decision")
        allocation, error = parse_allocation(text)
        if error:
            raise ValueError(f"{player}: {error}")
        count += 1
        departures += not single_json_allocation(text)
        return allocation, text, 0.0

    seed = player_seed(record["run_name"], record["treatment"], record["player_number"])
    result = run_player(record["treatment"], prompt_a, seed, answer)
    if next(replies, None) is not None:
        raise ValueError(f"{player}: unused recorded replies")
    # The JSON archive stores round numbers as string keys.
    result["rounds"] = {str(n): value for n, value in result["rounds"].items()}
    for key in ("seed", "rounds", "payment", "reversals", "messages", "unsent"):
        if result[key] != record[key]:
            raise ValueError(f"{player}: replay differs in {key}")
    return count, departures


def main():
    for condition in TREATMENTS:
        path = DATA / f"outline_{condition}.json"
        if build_outline(condition) != json.loads(path.read_text(encoding="utf-8")):
            raise ValueError(f"Replay differs from the archived outline for {condition}")
    players = replies = departures = 0
    with (DATA / "players.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                count, deviations = replay(json.loads(line))
                players += 1
                replies += count
                departures += deviations
    if not players:
        raise ValueError("The Milestone 2 archive contains no players")
    print(f"Matched {len(TREATMENTS)} outlines, {players} players and {replies} accepted replies.")
    print(f"{departures} accepted replies departed from the requested single-object format.")


if __name__ == "__main__":
    main()
