from prompt import prompt_a as prompts
from llm import LLM
from results import print_summary
from run import run_many
from treatments import TREATMENTS

RUN_NAME = "pilot_1"
PLAYERS_PER_TREATMENT = 3

#llm = LLM("openrouter", "<provider/model-id>")
llm = LLM("gemini", "gemini-3.1-flash-lite", temperature=1, requests_per_minute=10)
#llm = LLM("gemini", "gemini-3.5-flash-lite", temperature=1, requests_per_minute=10)

for treatment in TREATMENTS:
    run_many(RUN_NAME, treatment, llm, PLAYERS_PER_TREATMENT, prompts)

print_summary(RUN_NAME)
