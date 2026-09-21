"""Ollama Client and DeepSeek R1 Reasoning Model Sanitizer."""

import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from backend.app.config import settings

logger = logging.getLogger("deepseek_llm")


def strip_think_tags(text: str) -> str:
    """Strip DeepSeek R1 <think>...</think> reasoning tags and contents."""
    if not text:
        return ""
    # Remove complete <think>...</think> blocks (across multiple lines)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove unclosed <think> tag if text got truncated mid-reasoning
    cleaned = re.sub(r"<think>.*$", "", cleaned, flags=re.DOTALL)
    # Remove orphaned closing tags
    cleaned = cleaned.replace("</think>", "").strip()
    return cleaned


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Defensively extract JSON object from potentially conversational LLM output."""
    cleaned = strip_think_tags(text).strip()
    if not cleaned:
        return None

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Look for ```json ... ``` blocks
    json_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if json_block:
        try:
            return json.loads(json_block.group(1))
        except json.JSONDecodeError:
            pass

    # Look for outermost {...}
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None


class OllamaDeepSeekClient:
    """Async HTTP Client for local Ollama running deepseek-r1:8b over tunnel."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """Call Ollama /api/generate or /api/chat with timeout and error fallback."""
        url = f"{self.base_url}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("message", {}).get("content", "")
                    return strip_think_tags(content)
                else:
                    logger.warning(
                        "Ollama returned HTTP %d: %s. Using fallback parser.",
                        response.status_code,
                        response.text,
                    )
        except Exception as e:
            logger.warning(
                "Could not reach Ollama endpoint at %s (%s). Using defensive agent fallback.",
                self.base_url,
                str(e),
            )

        # Graceful fallback when Ollama tunnel is disconnected or offline
        return self._rule_based_fallback(prompt, system_prompt)

    def _rule_based_fallback(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Intelligent fallback when local Ollama tunnel is temporarily unreachable."""
        lower_prompt = prompt.lower()
        if "classify intent" in (system_prompt or "").lower():
            if any(k in lower_prompt for k in ["order", "pizza", "pasta", "drink", "food", "buy", "cart", "eat"]):
                return json.dumps({"intent": "order", "confidence": 0.95})
            if any(k in lower_prompt for k in ["reserve", "table", "book", "seat", "reservation"]):
                return json.dumps({"intent": "reservation", "confidence": 0.95})
            if any(k in lower_prompt for k in ["status", "where is", "track", "my order", "my reservation"]):
                return json.dumps({"intent": "status", "confidence": 0.95})
            if any(k in lower_prompt for k in ["hour", "time", "address", "location", "menu", "open", "phone"]):
                return json.dumps({"intent": "faq", "confidence": 0.95})
            return json.dumps({"intent": "general", "confidence": 0.8})

        return "Welcome to our restaurant! I can help you browse the menu, place an order, book a table, or check the status of your existing orders and reservations. How may I assist you today?"


ollama_client = OllamaDeepSeekClient()
