import os
import time
from typing import Dict, Any, Optional, Generator
from openai import OpenAI
from src.core.llm_provider import LLMProvider


# DEFAULT_MODEL = "meta-llama/llama-3-70b-instruct"
DEFAULT_MODEL = "meta-llama/llama-3-8b-instruct"

class OpenAIProvider(LLMProvider):
    def __init__(self, model_name: str = DEFAULT_MODEL, api_key: Optional[str] = None):
        super().__init__(model_name, api_key or os.getenv("OPENROUTER_API_KEY"))

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.3,
            top_p=0.9,
            max_tokens=512,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # ---- SAFE EXTRACTION ----
        if not response or not response.choices:
            return {
                "content": "Error: Empty response from model",
                "usage": {},
                "latency_ms": latency_ms,
                "provider": "openrouter-llama",
            }

        message = response.choices[0].message

        content = ""
        if message and message.content:
            content = message.content
        else:
            content = "Error: No content returned"

        usage = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) if response.usage else 0,
            "completion_tokens": getattr(response.usage, "completion_tokens", 0) if response.usage else 0,
            "total_tokens": getattr(response.usage, "total_tokens", 0) if response.usage else 0,
        }

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "openrouter-llama",
        }
    
    def stream(self, prompt: str, system_prompt: Optional[str] = None):
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta