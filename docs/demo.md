# Demo script

About 10 minutes on stage, plus about 45 minutes of preparation. What to
run, what to click, what to say, what to point at, and what to do if a step
is slow. Written for the demo on 2026-09-12; updated 2026-09-15 for the login and the Runtime agent.

Everything in the demo is about one document: the **Secure Transfers User
Guide** (`~/Downloads/Secure-Transfers-User-Guide.pdf`), a real 246-page
product manual used with permission. It covers projects, folders, user
roles, storage integrations and transfer protocols. The parser reads its
text; its screenshots are skipped. The three copies in Downloads are
identical; this one has the cleanest name.

Three terminals: **Terminal 1** for AWS commands, **Terminal 2** for the
backend, **Terminal 3** for the page.

---

## 45 minutes before

| Step | Run or click | You should see |
|---|---|---|
| 1. Start the graph (Terminal 1) | `aws neptune-graph start-graph --graph-identifier g-3h3xul06x6 --region us-west-2 --profile docs-copilot-dev` | `"status": "STARTING"`. If it says `ConflictException`, the graph is already starting or stopping: do not retry at once, go to step 2 |
| 2. Wait until it is ready (Terminal 1, every minute) | `aws neptune-graph get-graph --graph-identifier g-3h3xul06x6 --region us-west-2 --profile docs-copilot-dev --query status` | `"AVAILABLE"`, after 5 to 15 minutes. If it shows `"STOPPING"` or `"STOPPED"`, wait for `"STOPPED"`, then run step 1 again |
| 3. Start the backend (Terminal 2) | `cd ~/Projects/personal/Docs_Copilot/backend && uv run uvicorn app.main:app --port 8001` | `Uvicorn running on http://127.0.0.1:8001` |
| 4. Start the page (Terminal 3) | `cd ~/Projects/personal/Docs_Copilot/frontend && npm run dev` | `Local: http://localhost:3000` |
| 5. Open the page and the map | http://localhost:3000, **Sign in** with your own account, and the interactive map (link at the top of `docs/course.md`) | Cognito's login page, then the chat page with your email top right |
| 6. Upload the guide once now (only once step 2 says `"AVAILABLE"`) | in the page, **Upload a file**: `~/Downloads/Secure-Transfers-User-Guide.pdf` | "Indexing..." for a few minutes, then "Ready to ask ... The graph is updating in the background too." Skip if the guide is already listed under Documents |
| 7. Wait for the graph to finish reading it (Terminal 1, every minute) | `aws bedrock-agent list-ingestion-jobs --knowledge-base-id 3AD25HSRSD --data-source-id 6B3TDMPBRL --region us-west-2 --profile docs-copilot-dev --sort-by attribute=STARTED_AT,order=DESCENDING --max-results 1 --query 'ingestionJobSummaries[0].status'` | `"COMPLETE"`. The graph reads all 246 pages with an AI model, so it is slower than the page's own sync |
| 8. Warm-up question (not shown) | ask "What is SecureTransfers?" | an answer with source cards from the guide. The first question wakes everything up, so the demo's first answer is fast |
| 9. Clear the screen | click **New chat** | an empty chat, ready for the audience |

**Why upload it in preparation and again on stage:** the guide takes several
minutes to index, and the graph longer. Uploading it in preparation means
every question on stage works at once. On stage you upload the same file
again: it replaces the stored copy and runs a fresh sync the audience can
watch, while the questions are answered from the copy already indexed.

---

## The flow

### 1. The idea (1 minute, on the map)

Say: "Sign in, upload documents, ask questions, get answers with the exact
sources. Behind it is one AI agent, our code, hosted by AWS. For each
question it picks a tool: a document search, a knowledge graph, or a live
web browser. And it can only ever search the documents of the person
asking."

Point at: the four columns on the map, left to right: your laptop, the
agent, the tools, the data. Solid boxes are code we wrote; dashed boxes are
set up in AWS, with no code.

### 2. Upload the guide (1 minute)

Click **Upload a file**, choose `Secure-Transfers-User-Guide.pdf`.

Say: "The file goes to S3 with a small label next to it. Then two things
read it. The Knowledge Base cuts it into chunks, turns each chunk into a list
of numbers that captures its meaning, and indexes them. The graph Knowledge
Base also has an AI model pull out the things the manual names, like
projects, folders and roles, and how they connect."

Point at: the status line, "Indexing...". Do not wait for it: go on to step
3 while it runs. (If asked: the questions use the copy indexed before the
talk; this upload refreshes it.)

### 3. A document question (1 minute)

Ask: **"What are the steps to enable MFA for a user?"**

Point at:
- the line above the answer: "Searched your documents for ..."
- the numbered markers in the answer; open source card 1: the exact excerpt from the guide it came from
- the line under the answer: two model calls, one to decide which tool to use, one to write the answer

Say: "A 246-page manual. The search itself takes about a second; most of the
wait is the model writing."

### 4. A follow-up in the same chat (30 seconds)

Ask: **"Give me that in two bullet points."**

Say: "The page sent only this one line. The agent remembers the conversation
itself, in AgentCore Memory."

### 5. A relationship question: the graph (1 minute)

Ask: **"How do projects, folders and user roles relate to each other in SecureTransfers?"**

Point at: the line above the answer, "Searched the knowledge graph for ...".
Say: "A different tool. The graph search starts from the closest passages,
then follows connections to other passages that mention the same things."

If it used the document search instead: say that the agent chooses the tool
from each tool's description, and move on.

### 6. A question the guide cannot answer (30 seconds)

Ask: **"What is the capital of France?"**

Point at: the answer says the documents do not cover it, then answers from
general knowledge and says so. Say: "It never passes off general knowledge
as coming from your documents. That is one of its rules."

### 7. A live web page (1 minute)

Ask: **"What does https://aws.amazon.com/bedrock/agentcore/ say AgentCore is? Two sentences."**

Point at: "Opened https://...". Say: "A real browser that AWS runs in a
sandbox. The agent drives it step by step." Takes 30 to 60 seconds.

If it says it could not read the page: that is the honest-answer rule
working; say so.

By now the upload from step 2 has likely finished: point at "Ready to ask"
in the sidebar.

### 8. Under the hood (2 to 3 minutes, on the map)

Click **Document question** on the map and step through with the arrow keys.
Stop on three hops:
- hop 4, "FastAPI starts the agent": our code hands the question to AWS
- hop 7, "The agent calls the tool over MCP, as you": one standard plug for every tool, and the Gateway's policy checks the filter is yours
- hop 10, "FastAPI translates the stream": how the answer arrives piece by piece

Then click the **Gateway** box and read its "Acts as" line. Say: "Every call
is made by some identity, and that identity needs permission for exactly
that call."

### 8b. Two people (1 minute)

Click **Sign out**, sign in as the second account, and ask step 3's
question again.

Point at: an empty sidebar, and the answer "not in your documents". Say:
"Same question, different person, nothing leaks. The agent adds a filter
with the person's id to every search, and the Gateway's policy refuses any
search without it. That is a rule the model cannot talk its way around."
Sign back in as yourself.

### 9. Questions

Good answers to have ready:
- **Can it answer anything, or only the documents?** It searches your documents first, uses the browser for URLs and recent things, and answers general questions from its own knowledge while saying so. It remembers preferences you tell it across chats.
- **Cost:** a document question is about 1 cent; a web page 2 to 8 cents; indexing the guide a few cents. The graph is the only part billed by the hour: $0.48 an hour running, about 5 cents stopped.
- **Why this model:** Llama 4 could not use tools while streaming, and gpt-oss could not drive the browser. Mistral Large 3 did both (`docs/course.md` lesson 11).
- **What is ours and what is AWS:** our code is the page, the proxy, the FastAPI backend, the agent (200 lines of Python, hosted on AgentCore Runtime) and one Lambda. The login, the search, the graph, the memory, the browser and the policy engine are AWS services we set up.
- **Where does "only your documents" get enforced?** Twice. The agent adds the filter in code before every search. The Gateway's Cedar policy refuses a search whose filter is not the caller's id. Neither depends on the model behaving.

---

## Right after

1. Stop the graph (Terminal 1):
   ```
   aws neptune-graph stop-graph --graph-identifier g-3h3xul06x6 --region us-west-2 --profile docs-copilot-dev
   ```
2. Press Ctrl+C in Terminal 2 and Terminal 3 to stop the servers.

---

## If something breaks

| Symptom | Likely cause | Fix |
|---|---|---|
| "The backend is not reachable." | FastAPI is not running | step 3 of the preparation |
| every question fails with a 502 | AWS credentials expired or the wrong profile | run `aws sts get-caller-identity --profile docs-copilot-dev`; it should show your user |
| the page bounces to the login page again and again | the token expired (an hour), or the app client settings changed | sign in again; if it repeats, check `frontend/.env.local` against the Cognito console |
| questions find nothing, and Documents is empty | the guide was never uploaded in preparation | preparation step 6, then wait for "Ready to ask" |
| the relationship question errors, or says the tool failed | the graph is not `AVAILABLE` | preparation step 2; meanwhile skip to flow step 6 |
| the relationship question gives a thin answer, or uses the document search | the graph has not finished reading the guide | preparation step 7; wait until `"COMPLETE"` |
| preparation step 1 says `ConflictException` | the graph is already starting or stopping (one change at a time) | preparation step 2 until it settles; if `"STOPPED"`, run step 1 again |
| the graph "didn't start" and you don't know why | something else changed its state, or the start failed | AWS console, **CloudTrail**, **Event history**, filter by event name `StartGraph` or `StopGraph`: every call, who made it, when, and any error |
| the upload says "Another sync is running" | a sync was already going | nothing to do; the next sync picks the file up, and the questions still work from the copy already indexed |
| the first answer is slow | cold start | that is why preparation step 8 exists |
