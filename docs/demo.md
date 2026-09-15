# Demo script

About 10 minutes on stage, plus about 45 minutes of preparation. What to
run, what to click, what to say, what to point at, and what to do if a step
is slow. Written for a business audience: every step says the plain point
first, then one short line on how it works, for anyone who wants the
technical proof. Written for the demo on 2026-09-12; checked again on 2026-09-15.

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
| 5. Open the page and the map | http://localhost:3000, and the interactive map (link in `docs/course/README.md`) | the chat page and the map |
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

## Your story, on one page

Read this before the demo until you can say it without looking. The plain
words come first; the real names are there for when someone asks. Lesson
numbers point to `docs/course/`.

**The problem.** "Every team has long documents nobody wants to search:
manuals, policies, contracts. When someone needs one answer, they scroll,
search, or interrupt a colleague."

**What we built.** "Docs Copilot. You upload your documents, ask a question
in plain English, and get an answer in seconds, with a link to the exact
passage it came from. It can also read a web page for you, and connect facts
spread across a long manual."

**Why a business should care**

| They care about | What you say | Behind it, if asked | Lesson |
|---|---|---|---|
| Time | "An answer in seconds instead of minutes of scrolling." | the search itself takes about a second; most of the wait is the AI writing | 13 |
| Trust | "Every answer shows its source. You can check it in one click." | the answer is written only from the passages the search found, each numbered as a source | 13 |
| Cost | "About one cent per question." | pay-per-use AWS services; only the knowledge graph bills by the hour | 24 |
| Safety | "Your documents stay in your own private AWS storage, and the assistant says when something is not in them." | a private S3 bucket, a written rule in the prompt, and AWS roles that each allow one job | 9, 19 |

**How it works, in one breath.** "You ask a question. An AI assistant first
decides where to look: your documents, the connections inside them, or the
web. It finds the best passages, writes the answer from them, and shows you
where each part came from. It remembers the conversation, like a colleague
would."

**The parts, in plain words, with their real names**

| In plain words | Real name | Ours or AWS | Lesson |
|---|---|---|---|
| the chat page | a Next.js page with a small proxy that forwards to our server | ours, `frontend/` | 7 |
| the server that checks and forwards | the FastAPI backend on port 8001 | ours, `backend/app` | 5, 6 |
| the private file cabinet | an S3 bucket | AWS | 10 |
| the search that finds passages | a Bedrock Knowledge Base: meaning search plus exact-word search, then reranking | AWS | 13, 14 |
| the map of how things connect | a GraphRAG Knowledge Base on Neptune, billed by the hour | AWS | 15 |
| the assistant that decides and writes | the AgentCore Harness, running the Mistral Large 3 model | AWS | 11, 17 |
| the toolbox it reaches into | the AgentCore Gateway (an MCP server) and one small Lambda function of ours | AWS and ours | 18 |
| its memory | AgentCore Memory | AWS | 20 |
| its web reader | AgentCore Browser, a real Chrome in a sandbox | AWS | 21 |

**One question, step by step** (lesson 23 has the twelve-step version):

1. You type a question. The page sends just that question to our server (the FastAPI backend).
2. The server checks the request, so a bad one is refused before it costs anything, and passes it to the assistant (the AgentCore Harness).
3. The assistant reloads the conversation so far (AgentCore Memory) and asks the AI: "here are your rules, the question and your tools; what should we do?" (Mistral Large 3).
4. The AI decides: "search the documents for MFA steps".
5. The toolbox runs that search (the Gateway calls the Knowledge Base) and brings back the five best passages, each with its source file.
6. The AI writes the answer from those passages only, numbering each source [1], [2].
7. The answer appears word by word (streaming), with a line saying where it looked and a card for each source.
8. The conversation is saved. Later, background jobs note lasting preferences you stated, like "keep answers short".

That is why each answer shows "2 model calls": one to decide where to look,
one to write.

**Words you may use, plain meaning first**

- **AI assistant (agent):** an AI that can use tools, not just talk. It decides, a tool runs, it reads the result, and decides again.
- **Searching your documents first (RAG):** find the relevant passages, then give them to the AI with the question, so it answers from your documents instead of guessing.
- **Sources (citations):** the numbered markers and cards that show where each part of the answer came from.
- **Toolbox (MCP, the Gateway):** one standard plug between the assistant and its tools, so a new tool is configuration, not a rebuild.
- **Word by word (streaming):** the answer arrives as it is written, so you see the start almost at once.
- **Permissions (identity):** every part of the system can do exactly its one job and nothing else.

**Numbers worth knowing**

- A document question: about 1 cent, answered in seconds (2 model calls, 10 to 15 thousand tokens read).
- Reading a web page: 2 to 8 cents, because the AI reads the whole page (3 or 4 model calls).
- The connections map (the graph): $0.48 an hour while running, about 5 cents an hour stopped. Everything else is pay per use.
- What we built ourselves: about 1,600 lines of code on main, with 51 automated tests. The rest is AWS services we configured. The login branch adds about 600 lines and 22 tests.

**Questions business people ask, with the honest answer**

- *Why not just use ChatGPT?* "A public chat tool answers from what it learned on the internet, and cannot show you the passage an answer came from. This answers from your documents and points to the exact passage." If they push: the documents stay in your own AWS account, and every answer is tied to a search index you control.
- *Can it be wrong?* "Yes, like any assistant. That is why every answer shows its source, one click to check. And when the documents do not cover a question, it says so." If they push: two ways it fails, the search missed the passage or the AI misread it (lesson 13); measuring that with a set of test questions is the next step (lesson 29).
- *Is our data safe?* "The documents sit in private storage in our own AWS account, and each part of the system can do only its one job. This version is for one user. A second version adds sign-in, so each person can search only their own documents." If they push: AWS roles with one permission set each; the login branch uses Cognito sign-in and a policy check on every document search (Part H).
- *What does it cost?* "About a cent a question. Most parts cost nothing when nobody is using them." If they push: only the graph bills by the hour, so it is stopped when idle (lesson 24).
- *Why not build it all ourselves?* "The hard parts, the search, the memory, the assistant loop and a safe web browser, are services AWS already runs. We connected them and wrote the glue." If they push: lesson 25 lists what we tried and dropped.
- *Why this AI model?* "We tested three. Only one could both use its tools while answering live and read web pages reliably." If they push: Llama 4 could not use tools while streaming, and gpt-oss could not drive the browser; Mistral Large 3 did both (lesson 11).
- *What would it take to use this for a team?* "Three things: sign-in so each person has private documents, which is already built on a branch; running it on a server instead of a laptop; and a set of test questions to measure accuracy before and after every change."
- *What broke along the way?* "Plenty, and each failure shaped a decision." If they push: lesson 25 has the table.

---

## The flow

### 1. The problem and the promise (1 minute, on the map)

Say: "Every team has long documents nobody wants to search. Picture a new
support person who needs one answer from a 246-page product manual. Today
that means minutes of scrolling. Docs Copilot gives the answer in seconds,
and shows exactly where it came from."

Then: "Behind it is one AI assistant that AWS runs for us. For every
question it decides where to look: the documents, the connections inside
them, or the web."

Point at: the four columns on the map, left to right: your laptop, the
assistant, its tools, the data. Solid boxes are code we wrote; dashed boxes
are AWS services we set up.

### 2. Add the manual (1 minute)

Click **Upload a file**, choose `Secure-Transfers-User-Guide.pdf`.

Say: "I add the manual once. The system reads all of it, so later it can
find the right page in about a second."

Behind it: "It is stored privately, cut into short passages, and indexed by
meaning and by exact words. A second index also records how things in the
manual connect, like projects, folders and roles."

Point at: the status line, "Indexing...". Do not wait for it: go on to step
3 while it runs. (If asked: the questions use the copy indexed before the
talk; this upload refreshes it.)

### 3. Ask the manual a question (1 minute)

Ask: **"What are the steps to enable MFA for a user?"**

Say while it answers: "A plain question, the way a new employee would ask it."

Point at, in this order:
- the numbered markers in the answer; open source card 1. Say: "This is the exact passage it used. You never have to take its word for it." Pause here: this is the moment that earns trust.
- the line above the answer, "Searched your documents for ...". Say: "It decided on its own to search the manual."
- the line under the answer, "2 model calls". Say: "One to decide where to look, one to write the answer. About one cent."

### 4. A follow-up (30 seconds)

Ask: **"Give me that in two bullet points."**

Say: "I did not repeat the question. It remembers the conversation, like a
colleague would."

Behind it: "The page sends only the new line; the assistant reloads the
conversation from its memory service, AgentCore Memory."

### 5. How things fit together (1 minute)

Ask: **"How do projects, folders and user roles relate to each other in SecureTransfers?"**

Say: "A harder kind of question: not 'find the page', but 'how do these
pieces connect'. The answer is spread across the whole manual."

Point at: the line above the answer, "Searched the knowledge graph for ...".
Say: "So it picked a different tool: a map of how the things in the manual
connect to each other."

If it used the document search instead: say "It chooses the tool itself,
from a short description of each one; here it judged the normal search was
enough," and move on.

### 6. Something the manual does not cover (30 seconds)

Ask: **"What is the capital of France?"**

Point at: the answer says the documents do not cover it, then answers from
general knowledge and says so.

Say: "It never passes off general knowledge as coming from your documents.
That is one of its written rules, and it is what makes the sources worth
trusting."

### 7. Read a web page for me (1 minute)

Ask: **"What does https://aws.amazon.com/bedrock/agentcore/ say AgentCore is? Two sentences."**

Point at: "Opened https://...". Say: "It can also read a live web page and
summarize it."

Behind it: "AWS runs a real browser for it in a locked-down sandbox, so it
never touches this laptop. Without a link, for recent things, it searches
the web itself."

It takes 30 to 60 seconds. Fill the wait with: "It is actually opening the
page and reading it, step by step."

If it says it could not read the page: say "That is the honesty rule again:
it tells you instead of guessing."

By now the upload from step 2 has likely finished: point at "Ready to ask"
in the sidebar.

### 8. How it works, for the curious (1 to 2 minutes, on the map, optional)

Skip this if the room is not technical and time is short.

Say first: "In one sentence: our code is the chat page and a small server;
everything smart is AWS services we connected."

Click **Document question** on the map and step through with the arrow keys.
Stop on three hops, plain point first:
- hop 4, "FastAPI starts the agent": "Our server hands the question to the assistant AWS runs."
- hop 7, "The Harness calls the tool over MCP": "The assistant reaches its tools through one standard plug, so adding a tool is configuration, not a rebuild."
- hop 10, "FastAPI translates the stream": "The answer comes back piece by piece, which is why the words appear as it writes."

Then click the **Gateway** box and read its "Acts as" line. Say: "Every
part has permission for exactly its one job. That is how it stays safe as it
grows."

### 9. Close, then questions (1 minute)

Say: "So: answers in seconds, with the source every time, for about a cent a
question, and the documents stay in our own account. The next step is
sign-in, so each person searches only their own documents, and that is
already built."

Then take questions: the answers are in "Questions business people ask"
above.

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
| questions find nothing, and Documents is empty | the guide was never uploaded in preparation | preparation step 6, then wait for "Ready to ask" |
| the relationship question errors, or says the tool failed | the graph is not `AVAILABLE` | preparation step 2; meanwhile skip to flow step 6 |
| the relationship question gives a thin answer, or uses the document search | the graph has not finished reading the guide | preparation step 7; wait until `"COMPLETE"` |
| preparation step 1 says `ConflictException` | the graph is already starting or stopping (one change at a time) | preparation step 2 until it settles; if `"STOPPED"`, run step 1 again |
| the graph "didn't start" and you don't know why | something else changed its state, or the start failed | AWS console, **CloudTrail**, **Event history**, filter by event name `StartGraph` or `StopGraph`: every call, who made it, when, and any error |
| the upload says "Another sync is running" | a sync was already going | nothing to do; the next sync picks the file up, and the questions still work from the copy already indexed |
| the first answer is slow | cold start | that is why preparation step 8 exists |
