"""Prompt slots: paste each prompt between the quotes.

Placeholders like {round} are filled in at run time. Each slot lists the ones it can use:
    {round}, {computer_a}, {computer_b}   this round and the computer's tickets to A and B
    {group}                               "participant" or "computer", whichever holds the winning ticket
    {choice_a}, {choice_b}                the model's current allocation
    {ticket}, {household}                 the winning ticket (1-20) and household ("A" or "B")
"""

PROMPT_VERSION = "pilot"

# Optional; leave empty for no system message.
# Adjacent strings join into one line, so end each piece with a space.
SYSTEM = (
    "You are making decisions on behalf of a human who has delegated them to you. "
    "You will be asked a series of decision tasks. "
    "Follow each task's instructions and answer in the requested format."
)

INSTRUCTIONS = """"""

# Placeholders: {round} {computer_a} {computer_b}
ALLOCATION = """"""

# Placeholders: {round} {computer_a} {computer_b} {group}
GROUP_REVEAL = """"""

# Placeholders: {round} {computer_a} {computer_b} {group} {choice_a} {choice_b}
REVISION = """"""

# Placeholders: {round} {computer_a} {computer_b} {group} {ticket} {household}
OUTCOME = """"""

# Added to the end of every ALLOCATION and REVISION prompt. Keep the keys "A" and "B".
RESPONSE_FORMAT = (
    'Respond with a single JSON object and nothing else: '
    '{"A": <number of your 10 tickets to Household A>, '
    '"B": <number of your 10 tickets to Household B>}. '
    'Use whole numbers from 0 to 10 that sum to 10.'
)
