# Learning docs

Everything learned while building this project, written for someone new to
coding. Pictures over paragraphs. Every file ends with a self-check.

## How it is organized

```
tracks (grow forever, one section per topic)
  ai.md          models, tokens, RAG, embeddings, agents, MCP ...
  aws.md         account, IAM, Bedrock, S3, SQS, Cognito, ECS ...
  tooling.md     git, uv, ruff, mypy, Docker, CI ...
  web.md         HTTP, FastAPI, SSE, Next.js, TypeScript ...
  glossary.md    every new word, one table

build logs (one per deliverable)
  D1.md ... D8.md   what was built, the steps, what was verified,
                    links into the track sections that explain it
```

Rule: a topic has one home, in a track. A build log points at it, never
repeats it.

These files change. Sections get added, rewritten, merged, or deleted as
the project moves. If something is wrong or unclear, fix it in place.

## Reading order for a newcomer

1. `tooling.md` sections 1 and 2 (git, uv)
2. `aws.md` sections 1 to 5 (account, IAM, regions, budget, Bedrock)
3. `ai.md` sections 1 and 2 (what a model is, how to choose one)
4. `web.md` sections 1 to 7 (HTTP, FastAPI, streaming, errors)
5. `tooling.md` sections 6 to 8 (package layout, tests, type stubs)
6. `web.md` sections 8 to 11 (Next.js, the proxy, reading a stream)
7. `tooling.md` sections 9 and 10 (npm, Node's test runner)
8. `D1.md` (the build log that ties it together)
9. `ai.md` sections 3 to 6 (RAG, what happens inside it, GraphRAG, agents)
10. `aws.md` sections 6, 7 and 10 (S3, Knowledge Bases, AgentCore)
11. `ai.md` 2.7 (why the agent's model changed)
12. `D2.md` (documents, the agent, citations)
13. `D3.md` (browser, long-term memory) and `ai.md` 2.8 (why the model changed again)
14. `ai.md` section 5, then `D4.md` (GraphRAG)
