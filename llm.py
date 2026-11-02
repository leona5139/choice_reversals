"""To add a provider, write init_<name> and call_<name>, and add an elif for each below."""
import os
import time

from dotenv import load_dotenv

load_dotenv()


class LLM:
    def __init__(self, provider, model, temperature=1.0):
        self.provider = provider
        self.model = model
        self.temperature = temperature

        if provider == "openrouter":
            self.init_openrouter()
        elif provider == "gemini":
            self.init_gemini()
        else:
            raise ValueError(f"unknown provider: {provider}")

    def settings(self):
        return {"provider": self.provider, "model": self.model, "temperature": self.temperature}

    def chat(self, messages):
        start = time.time()

        if self.provider == "openrouter":
            reply = self.call_openrouter(messages)
        elif self.provider == "gemini":
            reply = self.call_gemini(messages)

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
