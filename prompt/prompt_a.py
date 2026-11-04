"""Prompt slots: paste each prompt between the quotes.

Copy this file to a new filename for each version. Keep used versions unchanged.

Placeholders like {round} are filled in at run time. Each slot lists the ones it can use:
    {round}, {computer_a}, {computer_b}   this round and the computer's tickets to A and B
    {group}                               "participant" or "computer", whichever holds the winning ticket
    {choice_a}, {choice_b}                the model's current allocation
    {ticket}, {household}                 the winning ticket (1-20) and household ("A" or "B")
"""

PROMPT_VERSION = __name__.rsplit(".", 1)[-1]

# Optional; leave empty for no system message.
# Adjacent strings join into one line, so end each piece with a space.
SYSTEM = (
    "You are participating in study of allocation behaviors. "
    "Follow the instructions for each round and make your own decisions."
)

INSTRUCTIONS = """

In this study, you will decide how to allocate chances to win $10 donations among actual households in Kenya.

There are eight rounds. Each round concerns two different recipient households, called Household A and Household B. You will not be given individual information that distinguishes A from B or indicates that one is more deserving of a donation.

Your decisions concern tickets 1-10, which can be assigned between A and B. The computer has already assigned tickets 11-20. You will see the computer's allocation for that round before making any allocation decision, and you cannot change it. One of the 20 tickets is selected at random for each round as the winning ticket: the household holding that ticket is the winner for that round.

Only one of the eight rounds will actually count. After all eight rounds are complete, one round will be selected at random, and a $10 donation will be made to that round's winning household. Treat each round as one that could count."""

# Placeholders: {round} {computer_a} {computer_b}
ALLOCATION = """Round {round}. In this round, the computer has already assigned {computer_a} of its 10 tickets to Household A and {computer_b} to Household B. Its allocation cannot be changed.

Assign your 10 tickets between Household A and Household B based on the information you have received for this round."""

# Placeholders: {round} {computer_a} {computer_b} {group}
GROUP_REVEAL = """For this round (Round {round}), the winning ticket has been put in the {group} set of 10 tickets (your tickets are 1-10; computer tickets are 11-20). Its specific number has not been revealed.

If it is in the computer set, the computer's existing allocation determines the winner and you have no further allocation decision for this round. If it is in your set, your allocation of tickets 1-10 can still determine which household wins."""

# Placeholders: {round} {computer_a} {computer_b} {group} {choice_a} {choice_b}
REVISION = """Earlier in Round {round}, you assigned {choice_a} of your tickets to Household A and {choice_b} to Household B. The computer assigned {computer_a} tickets to A and {computer_b} to B. You now know that the winning ticket is one of your tickets 1-10, but you do not know its specific number.

Review your earlier allocation. You may keep it or change it. Submit the allocation of your 10 tickets that you want to use for this round. To keep your earlier choice, submit the same numbers again."""

# Placeholders: {round} {computer_a} {computer_b} {group} {ticket} {household}
# TODO [OUTCOME FIDELITY] need to double check timing of OUTCOME prompt
OUTCOME = """Round {round} is complete. The winning ticket is in the {group} set of tickets."""

# Added to the end of every ALLOCATION and REVISION prompt. Keep the keys "A" and "B".
RESPONSE_FORMAT = (
    'Respond with a single JSON object and nothing else: '
    '{"A": <number of your 10 tickets to Household A>, '
    '"B": <number of your 10 tickets to Household B>}. '
    'Use whole numbers from 0 to 10 that sum to 10.'
)
