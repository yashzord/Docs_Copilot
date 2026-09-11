# Demo script

About 10 minutes. What to click, what to say, what to point at, and what
to do if a step is slow. Written for the demo on 2026-09-12.

---

## 30 minutes before

| Step | Command or click | You should see |
|---|---|---|
| 1. Start the graph | `aws neptune-graph start-graph --graph-identifier g-3h3xul06x6 --region us-west-2 --profile docs-copilot-dev` | status `STARTING` |
| 2. Wait until it is ready (repeat every minute) | `aws neptune-graph get-graph --graph-identifier g-3h3xul06x6 --region us-west-2 --profile docs-copilot-dev --query status` | `"AVAILABLE"` (5 to 15 minutes) |
| 3. Start the backend | `cd backend && uv run uvicorn app.main:app --port 8001` | `Uvicorn running on http://127.0.0.1:8001` |
| 4. Start the page | `cd frontend && npm run dev` | `Local: http://localhost:3000` |
| 5. Open the page and the map | http://localhost:3000 and the interactive map (link in `docs/learning/README.md`) | the chat page, empty; the map |
| 6. Load the starting documents | **Upload a file**: `README.md` (repo root), wait for "Ready to ask", then `docs/learning/aws.md`, wait again | both listed under Documents; "The graph is updating in the background too" |
| 7. Warm-up question (not shown) | ask "What is this project?" | an answer with source cards. The first call wakes everything up |

The bucket starts empty (fresh start on 2026-09-11), so step 6 is needed.
Keep `docs/learning/ai.md` for the live upload in the demo itself.

---

## The flow

### 1. The idea (1 minute, on the map)

Say: "Upload documents, ask questions, get answers with the exact sources.
Behind it is one AI agent that AWS runs for us. It picks a tool for each
question: a document search, a knowledge graph, or a live web browser."

Point at: the four columns on the map, left to right: your laptop, the agent,
the tools, the data. Solid boxes are our code; dashed boxes are AWS
configuration.

### 2. Upload a document live (1 minute)

Click **Upload a file**, choose `ai.md`.

Say: "The file goes to S3 with a small label next to it, then the Knowledge
Base reads it: cuts it into chunks, turns each chunk into numbers that
capture its meaning, and indexes them. The graph Knowledge Base also pulls
out the things it names and how they connect."

Point at: the status line, "Indexing..." then "Ready to ask".

If slow: keep talking through step 3 with `README.md`, which is already indexed.

### 3. A document question (1 minute)

Ask: **"What does the reranker do, and why is it needed after hybrid search?"**

Point at:
- the line above the answer: "Searched your documents for ..."
- the numbered markers in the answer, then open source card 1: the exact passage
- the token line: two model calls, one to decide, one to write

### 4. A follow-up in the same chat (30 seconds)

Ask: **"Give me that in two bullet points."**

Say: "The page sent only this one line. The agent remembers the conversation
in AgentCore Memory."

### 5. A relationship question: the graph (1 minute)

Ask: **"How do embeddings, hybrid search and the reranker relate to each other?"**

Point at: "Searched the knowledge graph for ...". Say: "Different tool. The
graph search starts from the closest passages, then walks to other passages
that mention the same things."

If it uses the document search instead: say the agent chose, and that the
tool description decides; move on.

### 6. A live web page (1 minute)

Ask: **"What does https://aws.amazon.com/bedrock/agentcore/ say AgentCore is? Two sentences."**

Point at: "Opened https://...". Say: "A real browser that AWS runs in a
sandbox, driven step by step by the agent." Takes 30 to 60 seconds.

If it says it cannot read the page: that is the honest-answer rule working;
say so.

### 7. Under the hood (2 to 3 minutes, on the map)

Click **Document question** on the map and step through with the arrow keys.
Stop on three hops:
- hop 4, "FastAPI starts the agent": our code hands over to AWS
- hop 7, "The Harness calls the tool over MCP": one standard plug for every tool
- hop 10, "FastAPI translates the stream": how the answer arrives word by word

Say: "Every call is made by some identity, and that identity needs permission
for exactly that call." Click the Gateway box: "Acts as".

### 8. Questions

Good answers to have ready:
- **Cost:** a document question is about 1 cent; a web page 2 to 8 cents; the graph is the only hourly part, $0.48 an hour running, stopped when idle.
- **Why these models:** Llama 4 could not use tools while streaming, gpt-oss could not drive the browser; Mistral Large 3 did both (`ai.md` 2.7, 2.8).
- **What is ours vs AWS:** our code is the page, the proxy, FastAPI and one Lambda; the agent, search, graph, memory and browser are configured.

---

## Right after

```
aws neptune-graph stop-graph --graph-identifier g-3h3xul06x6 --region us-west-2 --profile docs-copilot-dev
```

Stop both servers (Ctrl+C in each terminal).

---

## If something breaks

| Symptom | Likely cause | Fix |
|---|---|---|
| "The backend is not reachable." | FastAPI not running | step 3 above |
| every question fails with 502 | AWS credentials expired or wrong profile | `aws sts get-caller-identity --profile docs-copilot-dev` |
| relationship question errors or says the tool failed | graph not `AVAILABLE` | check step 2; use the document question instead |
| upload says "Another sync is running" | a sync was already going | wait a minute, it is picked up by the next sync |
| answer is slow the first time | cold start | that is why step 7 exists |
| "Upload a document on the left" and questions find nothing | the bucket is empty (fresh start) | step 6: upload `README.md` and `aws.md` |
