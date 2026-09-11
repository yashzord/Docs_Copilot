# Glossary

Every new word, one line, plain meaning. Alphabetical. Add as you go.

| Word | Plain meaning | Track |
|---|---|---|
| access key | username + password pair for programs to call AWS | aws |
| actor id | AgentCore Memory's name for the user a memory belongs to | aws |
| agent | a model in a loop: decide, call a tool, read the result, decide again | ai |
| agent loop | the code around the model that runs tool calls and feeds results back | ai |
| AgentCore | Bedrock's set of managed services for running agents. We use Harness, Gateway, Memory and the Browser tool; Identity and Runtime exist but are not used here | aws |
| API | a program other programs talk to over HTTP | web |
| App Router | Next.js's way of turning folders into URLs | web |
| ARN | Amazon Resource Name: the full address of one AWS resource, e.g. arn:aws:lambda:us-west-2:<account>:function:<name> | aws |
| async def | a function that says when it is waiting, so the server can serve others meanwhile | web |
| BFF | backend for frontend: a server route the page calls, which calls the real API | web |
| blocking | a call that holds the thread until it finishes (boto3 does this) | web |
| BM25 | the classic keyword scoring formula: rare query words appearing often in a chunk score high | ai |
| body | the data inside a request or response, JSON for us | web |
| BotoCoreError | boto3 error: never got a proper answer from AWS (network, config) | aws |
| bucket | a top-level container of files in S3, with a globally unique name | aws |
| budget | email alarm at a spending threshold, not a cap | aws |
| build system | the tool that turns code into an installable package. Our backend has none: it is run, not installed | tooling |
| catch-all route | a Next.js folder named `[...path]` that answers every URL below it; `params.path` is the list of parts | web |
| chunk | one piece of a document, a paragraph or so, the unit that gets searched and cited | ai |
| chunking | cutting a document into chunks; strategies: default, fixed-size with overlap, semantic, hierarchical | ai |
| CI | continuous integration: a robot runs lint, typecheck, tests on every push | tooling |
| citation | a mark in the answer pointing at the chunk that supports it | ai |
| client component | a React component that runs in the browser; the file starts with `"use client"` | web |
| ClientError | boto3 error: AWS answered, and the answer was an error | aws |
| commit | one saved snapshot of the repo | tooling |
| concurrency | many tasks in progress at once, taking turns. Threads waiting on the network give us this | web |
| content block | one piece of a model message (text, reasoning, a tool call, a tool result), streamed as start, deltas, stop | ai |
| context window | max tokens a model can hold in one call, everything included | ai |
| Converse API | Bedrock's chat API with one request shape for every model | aws |
| ConverseStream | the streaming form of Bedrock's Converse API; an agent needs a model that supports tool use in it | aws |
| CORS | the browser's rules for calling a different address than the page came from | web |
| cosine similarity | how close two vectors point; 1.0 same direction, 0 unrelated | ai |
| cross-encoder | a model that reads question and chunk together; what a reranker is | ai |
| data source | where a Knowledge Base gets documents: an S3 bucket, a web crawl | aws |
| data source sync | same as an ingestion job: the Knowledge Base re-reads the bucket; one at a time per data source | aws |
| dependency | a package our code needs to run | tooling |
| dependency (FastAPI) | a function FastAPI runs before the endpoint, via `Depends(...)` | web |
| dependency override | swapping a FastAPI dependency for another, used in tests | web |
| dev dependency | a tool needed to check the code, never shipped (ruff, pytest) | tooling |
| devDependencies | npm's list of tools needed only to check or build the code | tooling |
| embedding | a list of numbers representing a text's meaning; similar texts get similar numbers | ai |
| embedding model | outputs a list of numbers (a vector), not text. Used for search | ai |
| endpoint | one URL path + method the server answers, e.g. `POST /v1/chat` | web |
| entity | a thing named in text: a person, team, service, product. A node in the knowledge graph | ai |
| ESLint | the linter for JavaScript and TypeScript | tooling |
| eval set | fixed list of questions with known good answers, used to score models and RAG. This project has none yet | ai |
| event loop | the main thread's to-do loop in an async server: take a request, send a piece, repeat, never wait | web |
| event stream | a response that arrives as a series of small events | web |
| execution role | the IAM role a Harness or Runtime agent acts as | aws |
| faithfulness | eval score: does the answer follow from the cited text | ai |
| fake | a stand-in object used in tests instead of the real thing | tooling |
| FastAPI | Python library for building API servers | web |
| fixture | a pytest setup function that runs around tests | tooling |
| functional update | `setX(prev => ...)`: compute new state from the latest state | web |
| Gateway | AgentCore's managed MCP server: wraps APIs, Lambdas, Knowledge Bases and agents as tools | aws |
| GIL | Python's lock: one thread runs Python code at a time, but a thread waiting on the network steps aside | web |
| graph construction model | the model that reads each chunk during a GraphRAG sync and writes out things and their relationships (ours: Nova 2 Lite) | aws |
| graph walk | at query time, following the graph from the chunks a search found to other chunks that name the same things | ai |
| GraphRAG | RAG that also walks a knowledge graph of entities and relationships | ai |
| hallucination | the model states something its sources do not say | ai |
| Harness | AgentCore's managed agent: model, instructions, tools and memory declared as config | aws |
| header | a label on a request or response, e.g. `X-Tenant-Id: dev` | web |
| HNSW | a common index structure for fast approximate vector search | ai |
| HTTP method | the kind of request: GET reads, POST sends data | web |
| hybrid search | vector search and keyword search run together, results merged | ai |
| IAM | Identity and Access Management: who can do what in an AWS account | aws |
| IAM user | an identity inside the account with limited powers | aws |
| inference | one call to a model | ai |
| inference profile | a model's ID string on Bedrock. `us.` prefix means any US region may serve it | aws |
| ingestion job | the Knowledge Base's background run that reads new files and updates the index | aws |
| inline policy | a permission written directly on one role or user, not shared; used for the Lambda and Gateway roles in D4 | aws |
| input tokens | what you send: prompt, documents, history | ai |
| judge model | a model that scores other models' answers in an eval | ai |
| Knowledge Base | Bedrock's managed RAG service: ingest documents, answer Retrieve calls with chunks | aws |
| knowledge graph | nodes (entities) and edges (relationships) extracted from documents | ai |
| Lambda | AWS's run-code-on-demand service: you upload a function, AWS runs it per call, billed per call | aws |
| Lambda target | a Gateway target that turns a Lambda function into an MCP tool, described by a tool schema | aws |
| lint | automatic check for style mistakes and common bugs (ruff) | tooling |
| lockfile | exact versions of everything installed, so installs repeat | tooling |
| long-term memory | facts, summaries or preferences extracted from past sessions and searched later | ai |
| m-NCU | Neptune Analytics capacity unit: 1 GB of memory plus compute, billed per hour | aws |
| managed service | AWS runs it; you configure it, you do not operate servers | aws |
| MCP | Model Context Protocol: a standard way for agents to list and call tools | ai |
| metadata filter | restricting a search to chunks whose labels match, e.g. tenant_id | ai |
| MFA | phone code on top of a password | aws |
| model | text in, text out. Trained on huge amounts of text | ai |
| multipart form | the request body format for file uploads: parts separated by a boundary string | web |
| Neptune Analytics | AWS's graph engine; stores the GraphRAG graph; bills by the hour | aws |
| next typegen | generates Next.js's route and layout types without a full build. Run before `tsc` in CI | tooling |
| Next.js | a framework for building web apps with React | web |
| node_modules | installed npm packages. Never committed | tooling |
| npm | Node's package manager | tooling |
| object | one file in S3, stored under a key | aws |
| on-demand | pay per token, no commitment | aws |
| output tokens | what comes back. Usually 4 to 5x the price of input | ai |
| package | reusable published code, e.g. `fastapi` | tooling |
| package manager | downloads and installs packages. Ours is uv | tooling |
| package-lock.json | exact npm versions, like `uv.lock`. Committed | tooling |
| package.json | the frontend's list of packages and scripts, like `pyproject.toml` | tooling |
| parallelism | many tasks executing at the same instant on different CPU cores. The GIL blocks this for Python code | web |
| parametrize | run one test many times with different inputs | tooling |
| parsing | turning a PDF, HTML or Word file into plain text | ai |
| policy | JSON list of what an AWS identity may do | aws |
| process | one running program with its own memory. uvicorn is one process | web |
| profile | a named set of AWS credentials saved on the laptop | aws |
| prompt file | `backend/prompts/assistant.md`: the agent's system prompt, kept in git and pasted into the harness; its rules route questions to tools | ai |
| proxy | a server that forwards requests to another server | web |
| proxy allowlist | the fixed list of paths a proxy forwards, so it cannot be used to reach anything else | web |
| Pydantic | library that checks data against typed classes | web |
| RAG | retrieval-augmented generation: find relevant document chunks, hand them to the model, answer with citations | ai |
| React | a library for building UIs out of components | web |
| reasoning content | a model's thinking-out-loud text, streamed separately from the answer; we do not show it | ai |
| region | which group of AWS data centers a thing lives in | aws |
| remote | a copy of the repo elsewhere, usually GitHub, named `origin` | tooling |
| reranker | a careful model that re-sorts the top search results by how well each answers the question | ai |
| retrieval miss | the right passage was never found | ai |
| Retrieve | the Knowledge Base API call: question in, best chunks out | aws |
| retry | trying again automatically after a temporary failure | aws |
| root user | the AWS account owner login. Owner tasks only | aws |
| route | same as endpoint | web |
| route handler | a `route.ts` file in Next.js: an API endpoint, not a page | web |
| RRF | reciprocal rank fusion: merging two ranked lists by position, not score | ai |
| Runtime (AgentCore) | serverless hosting for agent code you write, uploaded as a zip or container | aws |
| self-managed Knowledge Base | a Knowledge Base where you choose the store, embeddings and chunking; the console calls it Unstructured Vector Store KB. Our graph one | aws |
| server component | a React component that runs on the server. The default in the App Router | web |
| service role | an IAM role an AWS service assumes to act on your behalf, e.g. the KB reading your bucket | aws |
| session | one conversation; in AgentCore, identified by a session id of 33+ characters | aws |
| short-term memory | the conversation so far, replayed into each model call | ai |
| sliding window | keep only the last N messages of a conversation in the model's context | ai |
| SSE | Server-Sent Events: plain-text events over one long HTTP response | web |
| static page | built once at build time and served as a file | web |
| status code | the server's one-number verdict: 200 ok, 4xx caller's fault, 5xx server's fault | web |
| stop reason | why the model stopped: end_turn (done) or tool_use (run this tool and come back) | ai |
| Strands Agents | AWS's open-source agent framework; the Harness is built on it | ai |
| streaming | sending a response in pieces as they are ready | web |
| streaming tool use | a model sending a tool call piece by piece; not every Bedrock model supports it (Llama 4 does not) | ai |
| system prompt | standing instructions sent with every model call, before the user's words | ai |
| Tailwind | styling with class names in the markup, e.g. `bg-indigo-600` | tooling |
| tenant label | the `.metadata.json` file next to each upload that tags its chunks with `tenant_id: dev`. Written on every upload, but no search filter uses it: the app has one user | aws |
| TextDecoderStream | browser tool that turns a stream of bytes into text, safely across chunks | web |
| thread | a line of work inside a process. Threads in one process share memory | web |
| thread pool | a set of worker threads that run blocking code off the main loop. 40 by default in FastAPI | web |
| token | about three quarters of a word. The billing unit for models | ai |
| tool call | the model asking for a tool by name with JSON arguments; the loop runs it | ai |
| tool schema | a tool's menu entry: name, description (what the agent reads to decide), input fields | ai |
| type stripping | Node removing TypeScript types so it can run a `.ts` file directly | tooling |
| type stubs | a package that describes another library's types to mypy | tooling |
| typecheck | automatic check that types line up (mypy) | tooling |
| useEffect | React: run code after the screen updates, e.g. scroll to the bottom | web |
| useState | React: a value that re-draws the component when it changes | web |
| uvicorn | the server program that runs a FastAPI app | web |
| validation | checking input against rules before using it | web |
| vector | a list of numbers; here, an embedding | ai |
| vector search | finding the chunks whose vectors are closest to the question's vector | ai |
| venv | a private folder of installed packages for one project | tooling |
| workspace | several Python packages sharing one venv and one lockfile. Not used yet | tooling |
