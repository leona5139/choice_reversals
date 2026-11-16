from prompt import prompt_a as prompts
from llm import LLM
from simulation.results import print_summary
from simulation.run import run_many
from simulation.treatments import TREATMENTS

RUN_NAME = "milestone_2"
PLAYERS_PER_TREATMENT = 20

LLMs = [
    # LLM("openrouter", "recursive/flint-v1.0:free", temperature=1),
    # LLM("gemini", "gemini-3.5-flash-lite", temperature=1, requests_per_minute=10),
    # LLM("gemini", "gemini-3.1-flash-lite", temperature=1, requests_per_minute=10),
    # LLM("openrouter", "openai/gpt-6-luna", temperature=1),
    LLM("openrouter", "google/gemma-4-31b-it", temperature=1, reasoning="off"),
    LLM("openrouter", "google/gemma-4-31b-it", temperature=1, reasoning="on"),
    LLM(
        "openrouter",
        "deepseek/deepseek-v4.1-flash-1017",
        temperature=1,
        reasoning="off",
    ),
    LLM(
        "openrouter",
        "deepseek/deepseek-v4.1-flash-1017",
        temperature=1,
        reasoning="high",
    ),
    LLM("openrouter", "anthropic/claude-haiku-5.5", temperature=1, reasoning="off"),
    LLM("openrouter", "anthropic/claude-haiku-5.5", temperature=1, reasoning="medium"),
    LLM("openrouter", "google/gemini-3.8-flash", temperature=1, reasoning="medium"),
    LLM("openrouter", "openai/gpt-6-luna", temperature=1, reasoning="off"),
    LLM("openrouter", "openai/gpt-6-luna", temperature=1, reasoning="medium"),
    LLM("openrouter", "qwen/qwen3.8-flash", temperature=1, reasoning="off"),
    LLM("openrouter", "qwen/qwen3.8-flash", temperature=1, reasoning="medium"),
]

for llm in LLMs:
    for treatment in TREATMENTS:
        run_many(RUN_NAME, treatment, llm, PLAYERS_PER_TREATMENT, prompts)

print_summary(RUN_NAME)
