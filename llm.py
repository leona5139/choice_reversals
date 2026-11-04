"""To add a provider, write init_<name> and call_<name>, and add an elif for each below."""
import os
import re
import threading
import time

from dotenv import load_dotenv

load_dotenv()


class LLM:
    def __init__(self, provider, model, temperature=1.0, requests_per_minute=None, rate_limit_waits=5):
        """requests_per_minute: shared across all threads; None means no limit.
        rate_limit_waits: how many times to wait out a 429 before giving up."""
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.min_interval = 60.0 / requests_per_minute if requests_per_minute else 0.0
        self.rate_limit_waits = rate_limit_waits
        self._lock = threading.Lock()
        self._next_slot = 0.0

        if provider == "openrouter":
            self.init_openrouter()
        elif provider == "gemini":
            self.init_gemini()
        else:
            raise ValueError(f"unknown provider: {provider}")

    def settings(self):
        return {"provider": self.provider, "model": self.model, "temperature": self.temperature}

    def wait_for_slot(self, extra_delay=0.0):
        """Reserves the next request slot (spaced min_interval apart) and sleeps until it."""
        with self._lock:
            now = time.monotonic()
            slot = max(now, self._next_slot, now + extra_delay)
            self._next_slot = slot + self.min_interval
        time.sleep(max(0.0, slot - now))

    def chat(self, messages):
        start = time.time()
        waits = 0

        while True:
            self.wait_for_slot()
            try:
                if self.provider == "openrouter":
                    reply = self.call_openrouter(messages)
                elif self.provider == "gemini":
                    reply = self.call_gemini(messages)
                break
            except Exception as error:
                text = str(error)
                is_rate_limit = "429" in text or "RESOURCE_EXHAUSTED" in text
                if not is_rate_limit or waits >= self.rate_limit_waits:
                    raise
                waits += 1
                match = re.search(r"retry in ([\d.]+)s", text)
                delay = float(match.group(1)) + 1 if match else 60.0
                # Push every thread's next slot back, not just this one.
                with self._lock:
                    self._next_slot = max(self._next_slot, time.monotonic() + delay)

        reply["seconds"] = round(time.time() - start, 2)
        return reply

    # OpenRouter

    def init_openrouter(self):
        from openai import OpenAI

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            max_retries=5,
        )

    def call_openrouter(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return {
            "text": response.choices[0].message.content,
            "cost": getattr(response.usage, "cost", None),
            "raw": response.model_dump(mode="json"),
        }

    # Gemini

    def init_gemini(self):
        from google import genai

        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def call_gemini(self, messages):
        config = {"temperature": self.temperature}
        contents = []

        for message in messages:
            if message["role"] == "system":
                config["system_instruction"] = message["content"]
                continue

            role = "model" if message["role"] == "assistant" else "user"

            # Gemini expects alternating turns, so back-to-back messages are joined.
            if contents and contents[-1]["role"] == role:
                contents[-1]["parts"][0]["text"] += "\n\n" + message["content"]
            else:
                contents.append({"role": role, "parts": [{"text": message["content"]}]})

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        return {
            "text": response.text,
            "cost": None,
            "raw": response.model_dump(mode="json"),
        }
