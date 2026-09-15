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
| 0. Use the login branch (Terminal 1, once) | `cd ~/Projects/personal/Docs_Copilot && git switch feat/login-runtime-agent && cp -n backend/.env backend/.env.main && cp backend/.env.branch backend/.env` | `Switched to branch 'feat/login-runtime-agent'`. The first copy keeps main's settings safe as `backend/.env.main` |
| 1. Start the graph (Terminal 1) | `aws neptune-graph start-graph --graph-identifier g-3h3xul06x6 --region us-west-2 --profile docs-copilot-dev` | `"status": "STARTING"`. If it says `ConflictException`, the graph is already starting or stopping: do not retry at once, go to step 2 |
| 2. Wait until it is ready (Terminal 1, every minute) | `aws neptune-graph get-graph --graph-identifier g-3h3xul06x6 --region us-west-2 --profile docs-copilot-dev --query status` | `"AVAILABLE"`, after 5 to 15 minutes. If it shows `"STOPPING"` or `"STOPPED"`, wait for `"STOPPED"`, then run step 1 again |
| 3. Start the backend (Terminal 2) | `cd ~/Projects/personal/Docs_Copilot/backend && uv run uvicorn app.main:app --port 8001` | `Uvicorn running on http://127.0.0.1:8001` |
| 4. Start the page (Terminal 3) | `cd ~/Projects/personal/Docs_Copilot/frontend && npm run dev` | `Local: http://localhost:3000` |
| 5. Open the page and the map | http://localhost:3000, **Sign in** with your own account, and the interactive map (link in `docs/course/README.md`) | Cognito's login page, then the chat page with your email top right |
| 5b. First sign-in, and a second person for flow step 8b (Terminal 1, once) | Your first sign-in asks for the temporary password from the invite email, then a new one. Second person: `aws cognito-idp admin-create-user --user-pool-id us-west-2_kMn6l3sGV --username <second email> --user-attributes Name=email,Value=<second email> Name=email_verified,Value=true --message-action SUPPRESS --region us-west-2 --profile docs-copilot-dev`, then `aws cognito-idp admin-set-user-password --user-pool-id us-west-2_kMn6l3sGV --username <second email> --password '<a password with a digit>' --permanent --region us-west-2 --profile docs-copilot-dev` | your email top right; the second account can sign in without any email |
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

## Know what you built, on one page

Read this before the demo until you can say it without looking. Every
line has a lesson number in `docs/course/` for the full story.

**The one sentence.** "Docs Copilot: sign in, upload documents, ask
questions, get answers with the exact sources, from one AI agent, our own
code hosted by AWS, that can also read live web pages. Every person's
document search, chats and memory are private to them."

**The pieces, and who made each one**

| Piece | What it is, in plain words | Ours or AWS | Lesson |
|---|---|---|---|
| the page | the chat window in the browser (Next.js). It sends your one message and draws the answer as it streams in | ours, `frontend/` | 7 |
| the proxy | a tiny door inside the page's server that forwards `/api/...` to the backend, so the browser never talks to AWS | ours, `frontend/app/api` | 7 |
| the login | Cognito's hosted sign-in page. The app never sees a password; it gets a token that every hop checks | AWS | 22 |
| the backend | the Python server (FastAPI) on port 8001: verifies your token, uploads files, calls the agent with your token, streams the answer back | ours, `backend/app` | 5, 6, 22 |
| S3 | the bucket where every uploaded file and its label live | AWS | 10 |
| the Knowledge Base | AWS's managed search over the files: it chunks, embeds and indexes each file, and answers "find me the passages about X" | AWS | 13, 14 |
| the graph Knowledge Base + Neptune | a second index that also extracts things and how they relate, for "how does X relate to Y" questions. Bills by the hour: started 45 minutes before, stopped after | AWS | 15 |
| the Gateway | the agent's tool menu (an MCP server): the Knowledge Base and the Lambda become two tools. It checks your token and asks its policy before every call | AWS | 18, 28 |
| the Lambda | 40 lines of ours that AWS runs on demand: it searches the graph Knowledge Base for the Gateway | ours, `infra/lambda` | 18 |
| the agent | 200 lines of Python (Strands) that AWS hosts on AgentCore Runtime in its own small machine per session. It runs the loop, calls the tools with your token, and adds the "only my documents" filter before every search | ours, `agent/src/main.py` | 17 |
| the policy | Cedar rules on the Gateway: a document search must carry the caller's own filter, or it is refused before it runs | AWS | 28 |
| the model | Mistral Large 3, called through Bedrock. The only part that "thinks" | AWS | 11 |
| Memory | every chat's messages, plus facts and preferences extracted from them, kept per user | AWS | 20 |
| the browser tool | a real Chrome in a sandbox that the agent drives to read a web page | AWS | 21 |

**One question, in eight steps** (lesson 23 has the twelve-step version):

1. You type a question. The page sends only that line, a chat id and your login token to the backend.
2. The backend verifies the token (no token, no call: refused before anything costs money) and calls the agent on Runtime with the same token.
3. Runtime verifies the token again, and our agent loads the chat so far from Memory under your id and asks the model: "here are the rules, the question, and your tools. What do you want to do?"
4. The model answers with a tool call: "search the documents for MFA steps".
5. The agent's hook adds the filter "only documents labelled with this person's id", then calls the Gateway with your token. The Gateway checks the token, its policy checks the filter is yours, and the Knowledge Base returns your five best passages.
6. The agent asks the model again: "here is the question and the passages. Answer, and cite them as [1], [2]."
7. The answer streams back through the backend and the proxy to the page, word by word, with the tool line above it and the source cards under it.
8. The agent saves the turn to Memory under your id. Minutes later, background jobs extract facts and preferences from it.

That is "2 model calls" under every answer: one to decide, one to write.

**Words you will say, and what they mean**

- **Agent:** a model in a loop with tools. The model never runs anything; it asks, the loop runs the tool and comes back.
- **Tool:** a function the agent may ask for: the document search, the graph search, the browser.
- **RAG:** find the relevant passages first, then hand them to the model with the question, so it answers from your documents instead of guessing.
- **Chunk, embedding, vector search:** documents are cut into paragraphs; each paragraph becomes a list of numbers that captures its meaning; a search finds the paragraphs whose numbers are closest to the question's.
- **Hybrid search and reranking:** meaning-search plus exact-word search, merged, then a careful second model re-sorts the top results.
- **MCP:** the standard plug between an agent and its tools. The Gateway speaks it.
- **Streaming:** the answer arrives in pieces, so the first word shows almost at once.
- **Identity:** every call is made by some identity that needs permission for exactly that call. Your login token is one identity, checked by the backend, by Runtime and by the Gateway; the agent's role and the Gateway's role are the others.
- **OAuth, 3-legged:** you sign in and consent on the login service's page, and the app gets a token to act for you. The 2-legged kind, a program signing in as itself, is not used here.

**Numbers worth knowing**

- A document question: about 1 cent, 2 model calls, 10 to 15 thousand tokens in.
- A web page: 2 to 8 cents, 3 or 4 model calls, the whole page's text goes into the model.
- The graph: $0.48 an hour running, about 5 cents an hour stopped. Everything else bills per use.
- Code we wrote: about 2,200 lines, plus 73 tests. The rest is AWS services we configured.

**Questions people ask, with the honest answer**

- *Why not just ask ChatGPT?* It has never seen your documents. This answers from them and shows you the exact passage.
- *Can it be wrong?* Yes. The citation is not proof, it is a pointer. Open the source card and check. Lesson 13 names the two failures: the search missed, or the model wrote something the passage does not say.
- *Why AWS managed services instead of building it?* Chunking, embeddings, hybrid search, reranking, memory, the agent loop, the browser: each would be weeks to build well. Configuring them took days and cost cents. Lesson 25 lists what we dropped.
- *Why this model?* Two others were tried: one could not use tools while streaming, one could not drive the browser. Mistral Large 3 did both.
- *Is it secure? Who can see my documents?* Only you. The agent adds a filter with your id to every search, and the Gateway's policy refuses any search without it. Proven with two accounts: same question, the other person gets nothing. One exception, say it out loud: the knowledge graph is shared, so a relationship question can quote anyone's uploads (lesson 28).
- *Why write your own agent instead of the managed one?* The managed Harness could not carry a person's login to the Gateway. Two hundred lines of our own code could, and that is what makes per-person privacy enforceable.
- *What would you do next?* Tracing of every step, guardrails on the model, and an evaluation set so changes are measured instead of eyeballed.
- *What broke along the way?* Plenty: lesson 25 has the table. The demo is the version that survived.

---

## The flow

### 1. The idea (1 minute, on the map)

Say: "Sign in, upload documents, ask questions, get answers with the exact
sources. Behind it is one AI agent, our code, hosted by AWS. For each
question it picks a tool: a document search, a knowledge graph, or a live
web browser. And its document search only ever sees the
documents of the person asking."

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
- hop 7, "The Harness calls the tool over MCP" (the map still draws the main version, so say "our agent, calling as you"): one standard plug for every tool, and the Gateway's policy checks the filter is yours
- hop 10, "FastAPI translates the stream": how the answer arrives piece by piece

Then click the **Gateway** box and read its "Acts as" line. Say: "Every call
is made by some identity, and that identity needs permission for exactly
that call."

### 8b. Two people (1 minute)

Needs preparation step 5b. Click **Sign out**, sign in as the second account, and ask step 3's
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
- **Why this model:** Llama 4 could not use tools while streaming, and gpt-oss could not drive the browser. Mistral Large 3 did both (lesson 11 in `docs/course/`).
- **What is ours and what is AWS:** our code is the page, the proxy, the FastAPI backend, the agent (200 lines of Python, hosted on AgentCore Runtime) and one Lambda. The login, the search, the graph, the memory, the browser and the policy engine are AWS services we set up.
- **Where does "only your documents" get enforced?** Twice. The agent adds the filter in code before every search. The Gateway's Cedar policy refuses a search whose filter is not the caller's id. Neither depends on the model behaving.

---

## Right after

1. Stop the graph (Terminal 1):
   ```
   aws neptune-graph stop-graph --graph-identifier g-3h3xul06x6 --region us-west-2 --profile docs-copilot-dev
   ```
2. Press Ctrl+C in Terminal 2 and Terminal 3 to stop the servers.
3. Before any demo of main: `git switch main && cp backend/.env.main backend/.env`.

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
