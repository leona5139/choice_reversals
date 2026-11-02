import json
import re


def parse_allocation(text):
    """Returns (choice, None) for a valid reply, or (None, error)."""
    json_blocks = re.findall(r"\{[^{}]*\}", text or "")
    if not json_blocks:
        return None, "no JSON object found"

    try:
        data = json.loads(json_blocks[-1])
    except json.JSONDecodeError as error:
        return None, f"invalid JSON: {error}"

    if set(data) != {"A", "B"}:
        return None, f'expected keys "A" and "B", got {sorted(data)}'

    a = data["A"]
    b = data["B"]
    if type(a) is not int or type(b) is not int:
        return None, f"tickets must be whole numbers, got A={a!r}, B={b!r}"
    if a < 0 or b < 0 or a + b != 10:
        return None, f"tickets must be 0-10 and sum to 10, got A={a}, B={b}"

    return {"A": a, "B": b}, None


def ask_with_retry(llm, messages, max_retries, log):
    """Resends the same messages until a reply parses. Returns (choice, text, cost)."""
    total_cost = 0.0
    errors = []

    for attempt in range(1, max_retries + 2):
        try:
            reply = llm.chat(messages)
            choice, error = parse_allocation(reply["text"])
            total_cost += reply["cost"] or 0
        except Exception as api_error:
            reply = None
            choice = None
            error = f"API error: {api_error}"

        log({"attempt": attempt, "messages": messages, "reply": reply, "choice": choice, "error": error})

        if choice is not None:
            return choice, reply["text"], total_cost
        errors.append(error)

    raise RuntimeError(f"no valid reply after {max_retries + 1} attempts: {errors}")


if __name__ == "__main__":
    examples = [
        ('{"A": 3, "B": 7}', True),
        ('Sure! Here is my choice: {"A": 5, "B": 5}', True),
        ('```json\n{"A": 10, "B": 0}\n```', True),
        ('{"A": 4, "B": 4}', False),
        ('{"A": 4.5, "B": 5.5}', False),
        ('{"A": 5}', False),
        ('{"A": 11, "B": -1}', False),
        ('I would split them evenly.', False),
        ('', False),
    ]
    for text, should_pass in examples:
        choice, error = parse_allocation(text)
        passed = (choice is not None) == should_pass
        print("ok  " if passed else "FAIL", repr(text), "->", choice or error)
