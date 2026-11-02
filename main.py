import prompts
from llm import LLM
from results import print_summary
from run import run_many
from treatments import TREATMENTS

RUN_NAME = "pilot_1"
PLAYERS_PER_TREATMENT = 3

llm = LLM("openrouter", "<provider/model-id>")
# llm = LLM("gemini", "<gemini-model-id>", temperature=1)

for treatment in TREATMENTS:
    run_many(RUN_NAME, treatment, llm, PLAYERS_PER_TREATMENT, prompts)

print_summary(RUN_NAME)
