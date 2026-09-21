"""Tests for DeepSeek R1 <think> Tag Stripping and Defensive JSON Parsing."""

import json
from backend.app.agent.llm import extract_json_from_text, strip_think_tags


def test_strip_think_tags_clean_block():
    """Verify clean stripping of <think>...</think> blocks."""
    raw = "<think>\nThinking about what the user said.\nThey want pizza.\n</think>I'd be happy to help with your pizza order!"
    cleaned = strip_think_tags(raw)
    assert cleaned == "I'd be happy to help with your pizza order!"
    assert "<think>" not in cleaned
    assert "</think>" not in cleaned


def test_strip_think_tags_unclosed_truncation():
    """Verify handling of unclosed <think> tag if model output got cut off."""
    raw = "<think>\nLet me analyze the tables available at Downtown..."
    cleaned = strip_think_tags(raw)
    assert cleaned == ""


def test_strip_think_tags_multiline_with_formatting():
    """Verify stripping when reasoning contains markdown and code."""
    raw = """<think>
Step 1: Check branch id = 1
Step 2: Table has capacity 4
```sql
SELECT * FROM tables;
```
</think>
Table confirmed for 4 guests!"""
    cleaned = strip_think_tags(raw)
    assert cleaned == "Table confirmed for 4 guests!"


def test_extract_json_direct():
    """Verify extraction of direct JSON."""
    raw = '{"intent": "order", "confidence": 0.9}'
    parsed = extract_json_from_text(raw)
    assert parsed is not None
    assert parsed["intent"] == "order"


def test_extract_json_embedded_in_markdown():
    """Verify extraction of JSON wrapped in markdown code blocks after think tags."""
    raw = """<think>
Let's format the response as JSON.
</think>
Here is the extraction:
```json
{
  "items": [
    {"menu_item_id": 1, "quantity": 2}
  ],
  "order_type": "delivery"
}
```
Have a nice day!"""
    parsed = extract_json_from_text(raw)
    assert parsed is not None
    assert len(parsed["items"]) == 1
    assert parsed["items"][0]["quantity"] == 2
    assert parsed["order_type"] == "delivery"


def test_extract_json_conversational_fallback():
    """Verify fallback when model produces no valid JSON."""
    raw = "<think>Hmm, nothing clear.</think>Just a plain conversational sentence without json."
    parsed = extract_json_from_text(raw)
    assert parsed is None
