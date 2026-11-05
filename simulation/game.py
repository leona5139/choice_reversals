"""Game rules. Tickets 1-10 belong to the participant, 11-20 to the computer."""

COMPUTER_TICKETS_TO_A = [7, 2, 10, 1, 8, 3, 9, 0]  # rounds 1-8, from Table 3 of the paper

ROUNDS_PER_BLOCK = 4
PARTICIPANT_WINS_PER_BLOCK = 2 


def computer_allocation(round_number):
    tickets_to_a = COMPUTER_TICKETS_TO_A[round_number - 1]
    return {"A": tickets_to_a, "B": 10 - tickets_to_a}


def same_block(round_a, round_b):
    return (round_a - 1) // ROUNDS_PER_BLOCK == (round_b - 1) // ROUNDS_PER_BLOCK


def draw_winning_ticket(rng, round_number, rounds):
    earlier_draws_in_block = [
        this_round["draw"]
        for other_round, this_round in rounds.items()
        if same_block(other_round, round_number) and this_round["draw"] is not None
    ]
    participant_wins = sum(1 for draw in earlier_draws_in_block if draw["group"] == "participant")

    wins_left = PARTICIPANT_WINS_PER_BLOCK - participant_wins
    rounds_left = ROUNDS_PER_BLOCK - len(earlier_draws_in_block)

    if rng.random() < wins_left / rounds_left:
        return {"group": "participant", "ticket": rng.randint(1, 10)}
    else:
        return {"group": "computer", "ticket": rng.randint(11, 20)}


def winning_household(draw, computer_allocation, participant_allocation):
    # Within each group, the lowest-numbered tickets go to household A.
    if draw["group"] == "participant":
        ticket_in_group = draw["ticket"]
        tickets_to_a = participant_allocation["A"]
    else:
        ticket_in_group = draw["ticket"] - 10
        tickets_to_a = computer_allocation["A"]

    if ticket_in_group <= tickets_to_a:
        return "A"
    else:
        return "B"
