"""Gateway tool "search_graph": search the GraphRAG Knowledge Base (Neptune Analytics).

The Gateway's Knowledge Base connector only accepts managed Knowledge Bases,
so this small Lambda sits in between:

    harness --MCP--> Gateway --invoke--> this function --Retrieve--> GraphRAG Knowledge Base

It answers in the same shape as the managed connector's Retrieve tool
({"retrievalResults": [...]}), so the chat relay turns its passages into
source cards without any change.

The Gateway calls lambda_handler(event, context) with the tool's arguments as
the event, e.g. {"query": "how does the Gateway relate to Memory?"}.
https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-add-target-lambda.html

Self-check (no AWS needed):  python handler.py
"""

# ruff: noqa: S101  (the self-check at the bottom is assert-based on purpose)

import os
from typing import Any

import boto3

# Set in the Lambda console, Configuration, Environment variables.
KB_ID = os.environ.get("GRAPH_KB_ID", "")
_kb = boto3.client("bedrock-agent-runtime")


def lambda_handler(event: dict[str, Any], context: Any, kb: Any = None) -> dict[str, Any]:
    query = str(event.get("query", "")).strip()
    if not query:
        return {"error": "query is required"}
    # GraphRAG: a vector search finds chunks, then the graph adds chunks linked to
    # them through shared entities (docs/learning/ai.md 5.2).
    # https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agent-runtime/client/retrieve.html
    response = (kb or _kb).retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": query[:1000]},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}},
    )
    return {"retrievalResults": [to_result(r) for r in response["retrievalResults"]]}


def to_result(hit: dict[str, Any]) -> dict[str, Any]:
    """One passage, labeled with its file name like the managed connector does."""
    uri = hit.get("location", {}).get("s3Location", {}).get("uri", "")
    return {
        "content": {"text": hit["content"]["text"]},
        "metadata": {"_document_title": uri.rsplit("/", 1)[-1] or "document"},
        "score": hit.get("score", 0.0),
    }


if __name__ == "__main__":

    class FakeKb:
        def retrieve(self, **kwargs: Any) -> dict[str, Any]:
            assert kwargs["retrievalQuery"] == {"text": "gateway and memory"}
            return {
                "retrievalResults": [
                    {
                        "content": {"text": "The Gateway exposes tools."},
                        "location": {"s3Location": {"uri": "s3://bucket/users/user-a/aws.md"}},
                        "score": 0.7,
                    }
                ]
            }

    out = lambda_handler({"query": " gateway and memory "}, None, kb=FakeKb())
    assert out == {
        "retrievalResults": [
            {
                "content": {"text": "The Gateway exposes tools."},
                "metadata": {"_document_title": "aws.md"},
                "score": 0.7,
            }
        ]
    }, out
    assert lambda_handler({}, None, kb=FakeKb()) == {"error": "query is required"}
    print("ok")
