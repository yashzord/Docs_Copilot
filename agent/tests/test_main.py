"""Tests for the agent's own logic: the per-user filter hook, the token's user id,
and the translation of Strands events. No model, no network."""

import base64
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("GATEWAY_URL", "https://example.test/mcp")
os.environ.setdefault("MEMORY_ID", "mem-test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import main


def token_with(sub: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"sub": sub}).encode()).decode().rstrip("=")
    return f"eyJhbGciOiJSUzI1NiJ9.{payload}.signature"


def test_user_id_is_the_sub_claim() -> None:
    assert main.user_id_from(token_with("user-a")) == "user-a"


def test_document_search_gets_the_users_own_filter() -> None:
    hook = main.OwnDocumentsOnly("user-a")
    event = SimpleNamespace(
        tool_use={"name": main.DOCS_TOOL, "input": {"retrievalQuery": {"text": "expenses"}}}
    )

    hook.add_filter(event)

    assert event.tool_use["input"] == {
        "retrievalQuery": {"text": "expenses"},
        "retrievalConfiguration": {
            "managedSearchConfiguration": {
                "filter": {"equals": {"key": "user-a", "value": "owner"}}
            }
        },
    }


def test_a_filter_the_model_wrote_is_replaced_not_kept() -> None:
    hook = main.OwnDocumentsOnly("user-a")
    event = SimpleNamespace(
        tool_use={
            "name": main.DOCS_TOOL,
            "input": {
                "retrievalQuery": {"text": "x"},
                "retrievalConfiguration": {
                    "managedSearchConfiguration": {
                        "filter": {"equals": {"key": "user-b", "value": "owner"}}
                    }
                },
            },
        }
    )

    hook.add_filter(event)

    key = event.tool_use["input"]["retrievalConfiguration"]["managedSearchConfiguration"]
    assert key["filter"]["equals"]["key"] == "user-a"


def test_other_tools_are_left_alone() -> None:
    event = SimpleNamespace(tool_use={"name": "graph___search_graph", "input": {"query": "x"}})

    main.OwnDocumentsOnly("user-a").add_filter(event)

    assert event.tool_use["input"] == {"query": "x"}


def test_translate_text_tool_result_and_usage() -> None:
    result = SimpleNamespace(
        metrics=SimpleNamespace(
            accumulated_usage={"inputTokens": 10, "outputTokens": 3}, cycle_count=2
        )
    )
    events = [
        {"data": "Hel"},
        {
            "message": {
                "role": "assistant",
                "content": [{"toolUse": {"name": "docs___Retrieve", "input": {"q": 1}}}],
            }
        },
        {
            "message": {
                "role": "user",
                "content": [{"toolResult": {"content": [{"text": "a"}, {"text": "b"}]}}],
            }
        },
        {"result": result},
        {"something_else": 1},
    ]

    out = [item for event in events for item in main.translate(event)]

    assert out == [
        {"type": "text", "text": "Hel"},
        {"type": "tool", "name": "docs___Retrieve", "input": {"q": 1}},
        {"type": "tool_result", "text": "ab"},
        {"type": "usage", "input_tokens": 10, "output_tokens": 3, "model_calls": 2},
    ]
