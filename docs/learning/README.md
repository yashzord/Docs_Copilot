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
2. `aws.md` sections 1 to 3 (account, IAM, Bedrock)
3. `ai.md` sections 1 and 2 (what a model is, how to choose one)
4. `D1.md`
