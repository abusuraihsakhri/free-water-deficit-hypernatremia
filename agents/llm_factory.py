"""
Legacy simulated-response adapter; no external model invocation is implemented.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Free Water Deficit Hypernatremia"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} simulated response]: No clinical or scientific verification was performed. Query received: '{prompt[:60]}...'."


class LLMFactory:
    """Returns a PHI-screened simulation, regardless of provider label."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Free Water Deficit Hypernatremia"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        elif prov in ["ollama", "local"]:
            return MockLLM(system_name)
        elif prov in ["claude", "anthropic"]:
            return MockLLM(system_name)
        elif prov in ["openai", "gpt4"]:
            return MockLLM(system_name)
        return MockLLM(system_name)
