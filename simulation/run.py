"""Runs players through a treatment's outline, one conversation per player.

Preview a treatment with the default prompt or specify a prompt module.
    uv run python -m simulation.run 2A2P_4AR
    uv run python -m simulation.run 2A2P_4AR prompt.prompt_a
"""
import importlib
import json
import os
import random
import re
import sys
import zlib
from concurrent.futures import ThreadPoolExecutor

from simulation import game
from simulation.parse import ask_with_retry
from simulation.results import RESULTS_ROOT, append_jsonl, load_players
from simulation.treatments import build_outline, describe, tasks_in

ROUND_PLACEHOLDERS = {"round", "computer_a", "computer_b"}
ALLOWED_PLACEHOLDERS = {
    "INSTRUCTIONS": set(),
    "ALLOCATION": ROUND_PLACEHOLDERS,
    "GROUP_REVEAL": ROUND_PLACEHOLDERS | {"group"},
    "REVISION": ROUND_PLACEHOLDERS | {"group", "choice_a", "choice_b"},
    "OUTCOME_A": ROUND_PLACEHOLDERS | {"group", "ticket", "household"},
    "OUTCOME_P": ROUND_PLACEHOLDERS | {"group", "ticket", "household"},
}
PLACEHOLDER_PATTERN = r"\{(\w+)\}"


class Conversation:
    """Information messages are held back until the next question, so the model
    never sees information that no later question depends on."""

    def __init__(self, system_prompt):
        self.messages = []
        self.unsent_information = []
        if system_prompt.strip():
            self.messages.append({"role": "system", "content": system_prompt})

    def add_information(self, text):
        self.unsent_information.append(text)

    def ask(self, question, get_answer):
        for text in self.unsent_information:
            self.messages.append({"role": "user", "content": text})
        self.unsent_information = []

        self.messages.append({"role": "user", "content": question})
        choice, reply_text, cost = get_answer(list(self.messages))
        self.messages.append({"role": "assistant", "content": reply_text})
        return choice, cost


def prompt_problems(prompts, outline):
    slots_needed = sorted({step["slot"] for step in outline if step["slot"]})
    problems = []

    for slot in slots_needed + ["RESPONSE_FORMAT"]:
        text = getattr(prompts, slot, "")
        if not text.strip():
            problems.append(f"{slot} is empty")

    for slot in slots_needed:
        used = set(re.findall(PLACEHOLDER_PATTERN, getattr(prompts, slot, "")))
        not_allowed = used - ALLOWED_PLACEHOLDERS[slot]
        if not_allowed:
            problems.append(f"{slot} uses {sorted(not_allowed)}; allowed: {sorted(ALLOWED_PLACEHOLDERS[slot])}")

    return problems


def final_allocation(this_round):
    return this_round["revision"] or this_round["initial"]


def placeholder_values(this_round):
    if this_round is None:
        return {}

    draw = this_round["draw"] or {}
    allocation = final_allocation(this_round) or {}
    return {
        "round": this_round["round"],
        "computer_a": this_round["computer"]["A"],
        "computer_b": this_round["computer"]["B"],
        "group": draw.get("group"),
        "ticket": draw.get("ticket"),
        "choice_a": allocation.get("A"),
        "choice_b": allocation.get("B"),
        "household": this_round["winner"],
    }


def fill_slot(prompts, slot, this_round):
    text = getattr(prompts, slot) or f"[EMPTY SLOT: {slot}]"
    values = placeholder_values(this_round)

    def replace(match):
        name = match.group(1)
        return str(values[name]) if name in values else match.group(0)

    return re.sub(PLACEHOLDER_PATTERN, replace, text)


def new_rounds(treatment):
    rounds = {}
    for round_number, task in enumerate(tasks_in(treatment), start=1):
        rounds[round_number] = {
            "round": round_number,
            "task": task,
            "computer": game.computer_allocation(round_number),
            "initial": None,
            "revision": None,
            "draw": None,
            "winner": None,
        }
    return rounds


def run_player(treatment, prompts, seed, get_answer):
    """get_answer(messages) returns (choice, reply_text, cost)."""
    rng = random.Random(seed)
    rounds = new_rounds(treatment)
    conversation = Conversation(prompts.SYSTEM)
    total_cost = 0.0
    payment_round = None

    for step in build_outline(treatment):
        this_round = rounds.get(step["round"])

        if step["only_if_winner"] and this_round["draw"]["group"] != step["only_if_winner"]:
            continue

        if step["kind"] == "message":
            conversation.add_information(fill_slot(prompts, step["slot"], this_round))

        elif step["kind"] == "ask":
            question = fill_slot(prompts, step["slot"], this_round) + "\n\n" + prompts.RESPONSE_FORMAT
            choice, cost = conversation.ask(question, get_answer)
            answer_field = "revision" if step["slot"] == "REVISION" else "initial"
            this_round[answer_field] = choice
            total_cost += cost

        elif step["kind"] == "draw":
            this_round["draw"] = game.draw_winning_ticket(rng, step["round"], rounds)

        elif step["kind"] == "resolve":
            this_round["winner"] = game.winning_household(
                this_round["draw"], this_round["computer"], final_allocation(this_round)
            )

        elif step["kind"] == "payment":
            payment_round = rng.choice(list(rounds))

    reversals = [
        this_round for this_round in rounds.values()
        if this_round["revision"] and this_round["revision"] != this_round["initial"]
    ]
    return {
        "treatment": treatment,
        "seed": seed,
        "rounds": rounds,
        "payment": {"round": payment_round, "household": rounds[payment_round]["winner"]},
        "reversals": len(reversals),
        "cost": total_cost,
        "messages": conversation.messages,
        "unsent": conversation.unsent_information,
    }


def player_seed(run_name, treatment, player_number):
    # Depends only on the treatment and player number, so every model sees the same draws.
    return zlib.crc32(f"{run_name}|{treatment}|{player_number}".encode())


def run_many(run_name, treatment, llm, n_players, prompts, max_retries=3, workers=4):
    """Saves each player as it finishes. Rerunning skips players that are already saved."""
    from tqdm import tqdm

    outline = build_outline(treatment)
    problems = prompt_problems(prompts, outline)
    if problems:
        raise ValueError(f"fix prompt module {prompts.__name__} first:\n  " + "\n  ".join(problems))

    folder = os.path.join(RESULTS_ROOT, run_name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, f"outline_{treatment}.json"), "w") as f:
        json.dump(outline, f, indent=2)

    setup = llm.settings()
    setup["prompt_version"] = prompts.PROMPT_VERSION or prompts.__name__

    def player_id(player_number):
        return f"{treatment}|{llm.model}|t={llm.temperature}|{setup['prompt_version']}|{player_number}"

    already_saved = {player["player_id"] for player in load_players(run_name)}
    to_run = [n for n in range(n_players) if player_id(n) not in already_saved]
    progress = tqdm(total=n_players, initial=n_players - len(to_run), desc=f"{treatment} {llm.model}")

    def run_one(player_number):
        this_id = player_id(player_number)
        player_setup = {**setup, "run_name": run_name, "player_number": player_number}

        def log_request(attempt):
            append_jsonl(os.path.join(folder, "requests.jsonl"), {"player_id": this_id, **player_setup, **attempt})

        def get_answer(messages):
            return ask_with_retry(llm, messages, max_retries, log_request)

        try:
            record = run_player(treatment, prompts, player_seed(run_name, treatment, player_number), get_answer)
        except Exception as error:
            progress.write(f"{this_id} failed and will rerun next time: {error}")
            return

        append_jsonl(os.path.join(folder, "players.jsonl"), {"player_id": this_id, **player_setup, **record})
        progress.update(1)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(run_one, to_run))
    progress.close()


def dry_run(treatment, prompts):
    example_answer = {"A": 5, "B": 5}

    def answer_with_example(messages):
        return example_answer, json.dumps(example_answer), 0.0

    outline = build_outline(treatment)
    record = run_player(treatment, prompts, seed=0, get_answer=answer_with_example)

    print(f"=== outline: {treatment} ===")
    print(describe(outline))

    print(f"\n=== conversation ({prompts.__name__}; every answer is {example_answer}) ===")
    for number, message in enumerate(record["messages"], start=1):
        print(f"\n[{number}] {message['role'].upper()}")
        print(message["content"])

    print("\n=== saved but never sent ===")
    for text in record["unsent"]:
        print(text)
    print(f"payment: {record['payment']}")

    problems = prompt_problems(prompts, outline)
    if problems:
        print("\n=== fix before a real run ===")
        for problem in problems:
            print(problem)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: uv run python -m simulation.run <treatment> [prompts_module]")
    prompts_module = sys.argv[2] if len(sys.argv) > 2 else "prompt.prompt_a"
    dry_run(sys.argv[1], importlib.import_module(prompts_module))
