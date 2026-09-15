# Glossary

Every word the course introduces, one line each. Alphabetical.

| Word | Plain meaning | Lesson |
|---|---|---|
| .gitignore | the file listing what git must not track, like `.env` and `node_modules/` | 2 |
| 2-legged OAuth | a program signs in as itself with a client id and secret; no person; the client credentials grant | 31 |
| 3-legged OAuth | a person signs in and consents; the program then acts on their behalf; the authorization code grant | 31 |
| A/B test | sending part of real traffic to a second version and comparing outcomes | 29 |
| A2A | Agent2Agent: an open protocol for one agent to hand tasks to another agent over HTTP | 18 |
| ABAC | attribute-based access control: rules compare facts about the user, the resource and the moment | 28 |
| absolute path | an address that starts from the top of the disk (`/`) or home (`~`), so it works from anywhere | 1 |
| access key | a username and password pair for programs to call AWS | 9 |
| access token | the short-lived token an API checks; ours is sent on every request and verified three times | 31 |
| actor id | AgentCore Memory's name for whose memory it is; the signed-in person's `sub` on the login branch, `dev` on main | 33 |
| agent | a model in a loop: decide, call a tool, read the result, decide again | 16 |
| AgentCore | AWS's set of managed services for running agents: Harness, Gateway, Memory, Browser, and more | 17 |
| AgentCore Identity | end-user logins (JWT inbound on Runtime and Gateway) and a token vault for agents; the branch uses the inbound half | 30 |
| agentic RAG | the model decides whether, where and what to search, by calling search as a tool | 13 |
| allowlist | a fixed list of what is permitted; the proxy forwards only `chat`, `documents`, `sessions` | 7 |
| answer relevance | whether the answer addresses the question asked | 29 |
| API | a program other programs talk to over HTTP | 4 |
| API key | a long secret string sent with each request that proves "this caller may use the API"; never expires unless rotated | 22 |
| app client | our page's registration with the Cognito user pool; public, so it has no secret | 31 |
| approximate nearest neighbour (ANN) | a vector index that takes shortcuts to find close vectors fast, occasionally missing the closest | 12 |
| architecture decision record (ADR) | a short numbered file for one decision: context, decision, consequences; replaced, never edited | 25 |
| arm64 | the processor instruction set of Graviton and Apple Silicon; AgentCore Runtime runs arm64 images | 32 |
| ARN | Amazon Resource Name: the full address of one AWS resource | 9 |
| ASGI | the Python standard for async servers; uvicorn speaks it | 5 |
| async def | a Python function that says when it is waiting, so the server can serve others meanwhile | 5 |
| audience | the service a token is meant for; token exchange narrows it to one service | 33 |
| authentication | proving who you are (password, key, token) | 9 |
| authorization | deciding what an authenticated identity may do | 9 |
| authorization code | the one-time code the login service sends back after sign-in, traded for tokens | 31 |
| authorization server | the login service that checks people and issues tokens; Cognito here | 31 |
| Availability Zone | one or more data centers inside a region, with their own power and network | 8 |
| bash | the long-time default shell on Linux | 1 |
| Bedrock Agents | AWS's older managed agent: instructions, attached Knowledge Bases, and action groups run by Lambda | 17 |
| BFF | backend for frontend: a server route the page calls, which calls the real API | 7 |
| bi-encoder | a model that encodes question and chunk separately; what an embedding model is; makes an index possible | 13 |
| Block Public Access | the S3 switch that stops any object from being made public | 10 |
| block storage | a virtual hard disk attached to one machine | 10 |
| blocking | a call that holds its thread until it finishes; boto3 does this | 5 |
| BM25 | the classic keyword score: frequent in the chunk, rare across all chunks, discounted for long chunks | 13 |
| body | the data inside a request or response | 4 |
| boto3 | the Python library for calling AWS | 5 |
| bounded autonomy | the agent decides freely inside a boundary it cannot change | 28 |
| branch | a named line of commits, so work can go on without touching `main` | 2 |
| bridge model | one shared app, a separate data store or index per tenant | 33 |
| bucket | a named container of files in S3 | 10 |
| budget | an email alarm at a spending line, not a cap | 8 |
| build vs buy | the choice between writing a piece yourself and using one someone else made or runs | 25 |
| catch-all route | a Next.js folder named `[...path]` that answers every URL below it | 7 |
| CDK | AWS Cloud Development Kit: write CloudFormation templates in a programming language | 8 |
| Cedar | AWS's open policy language; a policy names principal, action, resource and a condition | 28 |
| centralized version control | one server holds the full history and you commit straight to it (SVN, Perforce) | 2 |
| change data capture | indexing only what changed, by watching a source's change log | 14 |
| changelog | a dated list of user-visible changes per version | 25 |
| chaos engineering | injecting failures into a running system regularly, to prove it survives them | 26 |
| chatbot | one model call per message, no tools; knows only what it was trained on | 16 |
| chunk | one piece of a document, a paragraph or so: the unit that gets searched and cited | 13 |
| CI | continuous integration: a robot runs the checks on every push | 3 |
| citation | a mark like `[1]` in the answer pointing at the chunk that supports it | 13 |
| claim | one field inside a token: `sub`, `iss`, `client_id`, `token_use`, `exp` | 31 |
| CLI | the command line: driving a computer by typing commands | 1 |
| client component | a React component that runs in the browser; its file starts with `"use client"` | 7 |
| client credentials | the OAuth grant where a program trades its id and secret for a token for itself | 31 |
| closed weights | a model only its maker can run; you reach it over an API | 11 |
| cloud marketplace | a cloud service hosting many companies' models behind one API; Bedrock is one | 11 |
| CloudFormation | AWS's infrastructure as code service; builds a stack of resources from a template | 8 |
| CloudTrail | AWS's log of every API call in the account: who, what, when | 9 |
| CodeBuild | AWS's build-machine service; the AgentCore CLI builds our arm64 image there | 32 |
| Cognito | AWS's login service: user pools, a hosted login page, tokens | 31 |
| cold start | the delay when a Lambda runs after being idle and AWS has to start a fresh copy | 18 |
| commit | one saved snapshot of the project | 2 |
| community summary | Microsoft GraphRAG's model-written summary of a cluster of closely linked entities | 15 |
| compiled language | turned into the processor's own instructions before it runs (C, Go, Rust) | 3 |
| computer use | an agent that works a screen through screenshots, mouse clicks and typing | 21 |
| consent | the person agreeing, on the login service's page, that a program may act for them | 31 |
| container | a program packed with its dependencies into an image that runs the same on any machine | 32 |
| content block | one piece of a model message (text, reasoning, a tool call, a tool result), streamed as start, deltas, stop | 17 |
| context window | the most text a model can hold in one call | 11 |
| contextual grounding check | a Guardrail check that blocks an answer not supported by the retrieved passages | 28 |
| contextual retrieval | adding a model-written note about where a chunk sits in its document before indexing it | 13 |
| contrastive learning | how embedding models are trained: pull matching pairs together, push others apart | 13 |
| Conventional Commits | commit messages that start with `feat:`, `fix:`, `docs:` or `chore:` | 2 |
| Converse API | Bedrock's one request shape for chatting with any model, including tool calls | 17 |
| cookie | a small value the browser stores and sends back automatically; often holds a session id | 31 |
| corrective RAG | a grader checks retrieved passages and rewrites the query or searches elsewhere if they are weak | 13 |
| correlation id | another name for a request id, especially when it is passed between services | 23 |
| CORS | the browser rule that blocks a page from reading another origin's responses unless that server allows it | 7 |
| cosine similarity | how close two vectors point; 1.0 same direction, 0 unrelated | 12 |
| Cost Explorer | the AWS console page that shows spend grouped by service and time | 24 |
| cost per answer | the tokens and model calls one answer used, turned into money | 24 |
| credits | a dollar amount AWS gives an account, spent before any real bill | 8 |
| cross-encoder | a model that reads question and chunk together and scores relevance; what a reranker is | 13 |
| curl | a terminal program that sends a request and prints the response | 4 |
| DeepEval | an open-source Python framework for LLM checks written like unit tests | 29 |
| default deny | with no matching permit, the answer is no | 28 |
| defense in depth | stacking several independent safety layers so one failing is caught by the next | 28 |
| dependency (FastAPI) | a function FastAPI runs before the endpoint, asked for with `Depends(...)` | 5 |
| dependency group | packages needed only while developing, like `dev` in pyproject.toml | 3 |
| dependency override | swapping a dependency for a fake, used in tests | 5 |
| device code | the OAuth grant for TVs and command-line tools: approve on a phone with a short code | 31 |
| dimensions | how many numbers are in a vector; ours have 1,024 | 12 |
| discovery document | an OpenID provider's `/.well-known/openid-configuration`: its endpoints and key URL | 31 |
| distributed version control | every copy holds the full history; commit locally, push and pull (git) | 2 |
| Dockerfile | the recipe for a container image, one instruction per line | 32 |
| dot product | multiply matching numbers of two vectors and add; equals cosine for length-1 vectors | 12 |
| embedding | a list of numbers representing a text's meaning; similar texts get similar lists | 12 |
| end to end test | a test that drives the whole running app like a user (Playwright) | 3 |
| end-to-end test | a test that drives the whole running app the way a user would | 26 |
| endpoint | one URL path plus method the server answers | 4 |
| ENFORCE | policy engine mode that blocks denied tool calls | 34 |
| entity | a thing named in text: a person, team, service, product; a node in the knowledge graph | 15 |
| entity extraction | a model reading a chunk and writing out the things it names and how they relate | 15 |
| entrypoint | the function Runtime calls for each request to our agent, `chat()` | 32 |
| environment | one place the same code runs, with its own settings and data: local, staging, production | 26 |
| environment variable | a named setting (`NAME=value`) the shell hands to every program it starts | 1 |
| eval gate | a CI step that fails the build when eval scores drop below a threshold | 29 |
| eval set | a fixed list of questions with expected answers, used to score changes | 29 |
| eval set (golden set) | a fixed list of questions with expected answers, used to score a system | 29 |
| evaluator | a scorer, usually a judge model with a rubric, that grades answers or tool calls | 29 |
| event (Memory) | one stored message or piece of agent state in a conversation | 20 |
| event loop | one thread that juggles many waiting requests; code must `await` so it can switch | 5 |
| EventSource | the browser's built-in SSE reader; GET only, no body, reconnects by itself | 6 |
| explicit deny | a policy line that says Deny; it beats every Allow | 9 |
| FAISS | Meta's library for vector search in memory on one machine | 12 |
| faithfulness | does every claim in the answer follow from the retrieved passages | 29 |
| fake | a small working in-memory version of a real service, used in tests | 26 |
| FastAPI | the Python library our server is built with | 5 |
| fault injection | adding errors, delays or outages on purpose to see how a system copes | 26 |
| feature flag | an on/off switch in the code that hides a feature until it is ready | 2 |
| federation | a login pool trusting another provider (Google, a company's SAML) and still issuing its own tokens | 31 |
| few-shot example | a sample input with the exact output wanted, placed in the prompt to show a format | 19 |
| file storage | a shared network drive with folders, mounted by many machines | 10 |
| fine-tuning | training a model further on your own examples; good for behavior, poor for facts | 11 |
| fixed workflow | code decides the steps and the model only fills each one in | 16 |
| forbid wins | Cedar rule: any matching forbid beats every permit | 28 |
| formatter | a tool that rewrites code layout so every file looks the same (ruff format, prettier) | 3 |
| Gateway | AgentCore's managed MCP server; turns Knowledge Bases, Lambdas and APIs into tools | 18 |
| GenAI conventions | OpenTelemetry's agreed attribute names for model calls, like `gen_ai.usage.input_tokens` | 27 |
| GitFlow | a branching style with `develop`, `release/` and `hotfix/` branches around `main` | 2 |
| GitHub Actions | GitHub's CI service; our recipe is `.github/workflows/ci.yml` | 3 |
| graph database | a database that stores nodes and edges directly, so following a connection is fast | 15 |
| GraphQL | an API style with one URL where the client asks for exactly the fields it wants | 4 |
| GraphRAG | RAG that also walks a knowledge graph of entities and relationships | 15 |
| gRPC | an API style for service-to-service calls: a contract file, generated code, binary messages | 4 |
| Guardrail | Bedrock's checks on model input and output: content, topics, personal data, grounding | 28 |
| GUI | a graphical interface: windows, icons and a mouse | 1 |
| hallucination | the model states something its sources do not say | 13 |
| handoff | one agent passes the conversation to another agent for good | 16 |
| Harness | AgentCore's managed agent, declared as configuration; main's agent, replaced on the login branch by our own agent on Runtime | 30 |
| hash (password) | a one-way, deliberately slow function result stored instead of a password; bcrypt, scrypt, Argon2 | 31 |
| header | a label on a request or response, like `X-Tenant-Id: dev` | 4 |
| headless browser | a real browser run by a program, with no window on screen | 21 |
| hierarchical chunking | small child chunks for matching inside large parent chunks for reading | 13 |
| HNSW | the layered shortcut graph that makes vector search fast and approximate | 13 |
| hook | a function Strands runs at a fixed moment of the loop; ours sets the filter before every tool call | 32 |
| HTTP method | the kind of request: GET reads, POST sends data | 4 |
| human in the loop | the agent proposes an action and a person approves it before it runs | 16 |
| hybrid search | vector search and keyword search run together, results merged | 13 |
| HyDE | search with a model-written fake answer instead of the question | 13 |
| hydration | React in the browser attaching click handlers to HTML the server already rendered | 7 |
| IaaS | infrastructure as a service: rent virtual machines, disks and networks; you run everything above | 8 |
| IAM | Identity and Access Management: who may do what in an AWS account | 9 |
| IAM group | a named set of IAM users that share policies | 9 |
| IAM Identity Center | AWS's single sign-on: people log in once and get temporary credentials per account | 9 |
| IAM user | an identity for a person; ours is `yashubitra` | 9 |
| id token | the OpenID Connect token that tells the page who signed in, such as the email; never proof for an API | 31 |
| idempotent | sending a request twice leaves the same end state as sending it once | 4 |
| Identity (AgentCore) | logins for end users (JWT inbound) and a token vault for agents to reach other apps; not used here | 22 |
| identity provider | the product that plays authorization server: Cognito, Auth0, Okta, Entra ID, Keycloak | 31 |
| image | the packed file a container runs from, made of cached layers | 32 |
| implicit grant | a deprecated OAuth grant that returned tokens in the address bar | 31 |
| infrastructure as code | cloud resources described in files kept in git, created by a tool to match | 8 |
| ingestion job | the Knowledge Base's background run that reads new files; also called a sync | 14 |
| ingestion pipeline | the steps that turn raw files into searchable chunks: parse, chunk, embed, index | 14 |
| inline policy | a permission written directly on one role, not shared | 9 |
| integration test | a test that runs several parts together, often with outside services faked | 3 |
| interpreted language | read and run directly by an interpreter program (Python, JavaScript) | 3 |
| IVF | a vector index that groups vectors into clusters and searches only the nearest few | 12 |
| JSON | text shaped like `{"key": "value"}`; how programs exchange data | 4 |
| JWKS | the public keys a login provider publishes, used to verify its tokens' signatures | 31 |
| JWT | a signed token from a login provider that proves who the user is; checked by an inbound authorizer | 22 |
| JWT authorizer | a check on Runtime or a Gateway that accepts only valid tokens from a named provider and client | 32 |
| key (S3) | an object's full name inside a bucket, like `tenants/dev/guide.pdf` | 10 |
| Knowledge Base | Bedrock's managed search over documents: ingest files, answer Retrieve calls with chunks | 14 |
| knowledge graph | nodes (entities) and edges (relationships) extracted from documents | 15 |
| Lambda | AWS's run-code-on-demand service; you upload a function, AWS runs it per call | 18 |
| layer | one cached snapshot in an image, one per Dockerfile instruction | 32 |
| layout-aware parsing | parsing that keeps headings, columns and tables as structure | 14 |
| least privilege | give each identity only the permissions it needs | 9 |
| LightRAG | an open-source GraphRAG variant with a lighter graph index and no community summaries | 15 |
| lint | an automatic check for style mistakes and common bugs | 3 |
| Llama Guard | Meta's open-weight model that classifies prompts and answers as safe or unsafe | 28 |
| LLM as a judge | a model that scores answers against a rubric | 29 |
| LLM observability | tracing tools shaped for model calls: prompts, answers, tokens, cost, scores (Langfuse, LangSmith, Arize Phoenix) | 27 |
| localhost | the name a machine uses for itself | 3 |
| lock-in | how hard it is to leave a service or vendor once you depend on it | 25 |
| lockfile | the exact versions of everything installed, so installs repeat | 3 |
| log | one timestamped line of text written when something happens | 27 |
| LOG_ONLY | a policy mode that records decisions without blocking | 28 |
| long context | sending whole documents in a very large context window instead of searching | 13 |
| long polling | the client asks, the server holds the request open until there is news, then the client asks again | 6 |
| long-term memory | preferences, facts and summaries extracted from past chats and searched later | 20 |
| m-NCU | Neptune Analytics capacity unit; billed per hour | 15 |
| machine identity | an identity for a program, not a person: a role, service account or API key | 22 |
| managed agent runtime | hosting built for agents: one isolated session per conversation, caller checked at the door | 32 |
| managed identity | Azure's identity for a service; the counterpart of an AWS role | 9 |
| managed login | Cognito's hosted sign-in page, so the app never handles passwords | 31 |
| managed service | AWS runs it; you configure it, you operate no servers | 8 |
| MCP | Model Context Protocol: a standard way for agents to list and call tools | 18 |
| Mem0 | an open-source and hosted memory layer that extracts and stores facts about users | 20 |
| merge | joining one branch's commits into another | 2 |
| merge conflict | both branches changed the same lines, so a human must choose | 2 |
| metadata filter | restricting a search to chunks whose labels match | 10 |
| metric | a number counted over time, such as error rate or tokens per hour | 27 |
| MFA | multi-factor authentication: a second proof, like a code from a phone app | 9 |
| middleware | a function every request passes through before the route, like logging or a login check | 5 |
| mock | a test stand-in that returns answers and checks it was called the expected way | 26 |
| model | text in, text out; trained on huge amounts of text | 11 |
| model routing | sending each question to the cheapest model that can handle it | 24 |
| moto | a Python library that fakes AWS services such as S3 in tests | 3 |
| multi-hop question | a question whose answer needs several connected facts from different passages | 15 |
| multi-query | searching with several phrasings of one question and merging the results | 13 |
| multi-tenancy | one running app serving many tenants whose data must stay apart | 30 |
| multipart form | the request body format for file uploads | 10 |
| naive RAG | chunk, embed, take the top few by vector search, paste into the prompt | 13 |
| NeMo Guardrails | NVIDIA's open-source toolkit for programmable guardrails around any model | 28 |
| Neo4j | the most widely used graph database; queried with Cypher | 15 |
| Neptune Analytics | AWS's graph database engine; stores the GraphRAG graph; bills by the hour | 15 |
| next-token prediction | how a model writes: score every possible next token, pick one, repeat | 11 |
| Next.js | a framework for building web pages with React | 7 |
| normalize | scale a vector to length 1 so only its direction counts | 12 |
| NoSQL database | items looked up by key or flexible documents, spread over many machines | 10 |
| OAuth 2.0 | the standard for letting one program act for you at another without your password | 31 |
| OAuthUser | the Cedar principal for a caller with a login token; its `id` is the person's `sub` | 34 |
| object | one file in S3, stored under a key | 10 |
| object metadata | name-value pairs S3 stores with an object, like its content type | 10 |
| object storage | whole files stored under keys in a bucket, read and written over HTTP | 10 |
| observability | metrics, logs, traces and quality scores about a running system | 27 |
| OCR | optical character recognition: reading letters out of a picture of text | 14 |
| offline evaluation | scoring a fixed eval set before release | 29 |
| on behalf of | a program holding a person's token calling a further program as that person | 33 |
| on-demand | billed per hour or second while a resource exists, no commitment | 8 |
| on-premises | you own and run the machines in your own building | 8 |
| online evaluation | scoring real, live traffic after release | 29 |
| OPA / Rego | Open Policy Agent, a general policy engine, and its rule language | 28 |
| open weights | a model whose learned numbers are published, so anyone can run it | 11 |
| OpenAPI | a standard machine-readable description of an API; FastAPI serves ours at `/openapi.json` | 5 |
| OpenFGA | an open-source authorization service in the style of Google's Zanzibar, for relationship-based rules | 28 |
| OpenID Connect | the layer on OAuth that says who signed in, with an id token and a discovery document | 31 |
| OpenTelemetry | the open standard for traces, spans and metrics; AgentCore emits it | 27 |
| OpenTelemetry (OTel) | the open standard for producing and shipping logs, metrics and traces to any tool | 27 |
| orchestrator | software that keeps container copies running, replaces crashed ones, rolls out versions; ECS, Kubernetes | 32 |
| origin | scheme plus host plus port, like `http://localhost:3000`; the unit browsers use for cross-site rules | 7 |
| overlap | text shared by neighboring chunks so a sentence at an edge is not lost | 13 |
| PaaS | platform as a service: hand over your app, the platform runs the servers | 8 |
| package | published code you install instead of writing, like `fastapi` | 3 |
| package manager | downloads and installs packages: uv for Python, npm for JavaScript | 3 |
| passkey | a per-site key pair on your device that replaces a password and resists phishing (WebAuthn) | 31 |
| path | which thing a request is about, like `/v1/chat`; also an address on disk | 1, 4 |
| path parameter | a slot in a URL path read as a value, like `{job_id}` | 4 |
| pgvector | the Postgres extension that adds a vector column and vector search | 12 |
| PII masking | hiding personal data such as emails in model input or output | 28 |
| PKCE | a per-sign-in secret whose hash goes first, so a stolen authorization code is useless | 31 |
| Playwright | a library that drives Chrome, Firefox or WebKit from code | 21 |
| policy | a JSON list of what an AWS identity may do | 9 |
| policy engine | a set of Cedar policies attached to a Gateway that judges every tool call | 28 |
| polling | the client asks again on a timer; the sidebar checks a sync every 5 seconds | 6 |
| pool model | one shared data store where every item carries a tenant label and every query filters on it | 33 |
| port | a numbered door on a machine; our API is on 8001, the page on 3000 | 3 |
| PowerShell | Microsoft's shell, passing objects between commands instead of text | 1 |
| prefix | the start of an S3 key, used like a folder | 10 |
| presigned URL | a link signed with someone's credentials that allows one upload or download until it expires | 10 |
| process | a running program, with its own number (PID) | 1 |
| production | the environment real users use, with real data and real money | 26 |
| profile | a named set of AWS credentials saved on the laptop; ours is `docs-copilot-dev` | 9 |
| prompt caching | a provider feature that bills a repeated prompt beginning at a reduced rate | 24 |
| prompt injection | text that tricks a model into following instructions that are not the operator's; direct from the user, indirect from content it reads | 19 |
| promptfoo | an open-source command-line tool that tests and compares prompts and models from a config file | 29 |
| proxy | a server that forwards requests to another server | 7 |
| public client | an OAuth client that cannot keep a secret, such as a page in a browser | 31 |
| pull request | a request to merge a branch into `main`, reviewed and checked by CI first (GitLab: merge request) | 2 |
| Pydantic | the library that checks data against typed classes | 5 |
| query rewriting | a model turning the user's words into a better search query | 13 |
| RAG | retrieval-augmented generation: find relevant chunks, hand them to the model, answer with citations | 13 |
| RAG triad | context relevance, faithfulness, answer relevance: the three scores that cover most RAG failures | 29 |
| RAGAS | an open-source Python library of RAG evaluation metrics | 29 |
| RBAC | role-based access control: users get roles, roles get permissions | 28 |
| React | a library for building web pages out of components | 7 |
| ReBAC | relationship-based access control: permissions follow a graph of who is connected to what | 28 |
| recorded response | a real service response captured once and replayed in tests | 26 |
| recursive chunking | split on paragraphs, then sentences, then words, until pieces are small enough | 13 |
| refresh token | a long-lived token for getting a new access token without signing in again; not used here | 31 |
| region | which group of AWS data centers a thing lives in; ours is us-west-2 | 8 |
| relative path | an address that starts from the folder you are in | 1 |
| remote | another copy of the git history yours pushes to and pulls from; the default name is origin | 2 |
| request header allowlist | the Runtime setting naming headers passed through to the agent's code; ours is `Authorization` | 32 |
| request id | an id given to one request and written in every log line about it | 23 |
| reranker | a careful model that re-sorts the top search results by how well each answers the question | 13 |
| reserved capacity | a one- or three-year promise of use in exchange for a discount; savings plans are the same idea | 8 |
| resource server | the program that holds what the person wants and checks the token; FastAPI, Runtime, the Gateway | 31 |
| response caching | storing an answer so the same question is answered without calling the model | 24 |
| REST | an API style: a path per thing, methods for actions, status codes for outcomes | 4 |
| retrieval precision | of the passages found, the share that were useful | 29 |
| retrieval recall | of the passages that should have been found, the share that were | 29 |
| Retrieve | the Knowledge Base call: question in, best chunks out | 14 |
| role | an AWS identity for a service; no password, assumed automatically | 9 |
| root user | the AWS account owner login; owner tasks only | 9 |
| RRF | reciprocal rank fusion: merge two ranked lists by position, 1 / (k + rank) | 13 |
| Runtime (AgentCore) | the hosting service for agent code: one isolated machine per session, checks the caller, streams the output | 32 |
| S3 | AWS's file storage | 10 |
| S3 Vectors | AWS's low-cost vector storage in S3-style buckets | 12 |
| SaaS | software as a service: a finished product you log into | 8 |
| salt | a random value added per user before hashing a password, so equal passwords hash differently | 31 |
| SAML | an older XML standard for enterprise single sign-on | 31 |
| search API | a paid web service that returns search results as JSON for programs | 21 |
| self-hosting | running an open-weights model on your own GPUs | 11 |
| Self-RAG | the model judges whether to retrieve and whether its answer is supported, then retries | 13 |
| semantic cache | a response cache that also matches questions with the same meaning in other words | 24 |
| semantic chunking | cut where the meaning shifts, found by embedding neighboring sentences | 13 |
| sequence diagram | a drawing of who calls whom, in order, with time running downwards | 23 |
| server | a program that waits for requests and answers them | 3 |
| server component | a React component that runs on the server; the default in Next.js | 7 |
| server-side rendering (SSR) | the server builds a page's HTML on each request | 7 |
| serverless | nothing of yours runs between requests; code or a managed service runs and bills per request | 8 |
| service account | Google Cloud's identity for a service; the counterpart of an AWS role | 9 |
| session | one conversation; identified by an id of 33 or more characters | 17 |
| session (web login) | a server-side record of a signed-in user, found through a session id in a cookie | 31 |
| session manager | Strands' plug for where messages live; ours reads and writes AgentCore Memory | 32 |
| shell | the program inside the terminal that reads a command and starts the program named | 1 |
| short-term memory | the conversation so far, replayed into each model call | 20 |
| Signature Version 4 | how AWS requests are signed with a secret key without sending the secret | 9 |
| SigV4 | Signature Version 4: how AWS requests are signed with a secret-derived key, so the secret never travels | 22 |
| silo model | a separate stack or account per tenant | 33 |
| single sign-on (SSO) | one login that opens many accounts or apps | 9 |
| single-page app (SPA) | one HTML shell; JavaScript in the browser draws every screen | 7 |
| sliding window | keeping only the last N messages of a chat in the model's input | 20 |
| smart parsing | the managed Knowledge Base's own parsing strategy (`SMART_PARSING`) | 14 |
| span | one unit of work in a trace: a name, a start, a duration, attributes | 27 |
| spot | spare capacity at a deep discount that AWS can take back at short notice | 8 |
| spy | a test stand-in that records calls so the test can check them afterwards | 26 |
| SQL database | tables of rows and columns queried with SQL; PostgreSQL is the common choice | 10 |
| SSE | Server-Sent Events: plain-text events over one long HTTP response | 6 |
| SSO | single sign-on: one login opens many apps | 31 |
| stack | a group of resources CloudFormation created from one template, managed together | 8 |
| staging | a copy of production with fake data, for final checks before release | 26 |
| staging area | the files picked with `git add` for the next commit | 2 |
| stateless | each request stands alone; the server keeps nothing between them unless the request points to it | 4 |
| static generation | page HTML built once at build time and served as files | 7 |
| status code | the server's one-number verdict: 200 ok, 4xx caller's fault, 5xx server's fault | 4 |
| stdio (MCP) | the local MCP transport: the agent starts the server as a child program and talks over standard input and output | 18 |
| stop reason | why the model stopped: `end_turn` (done) or `tool_use` (run this and come back) | 16 |
| storage class | an S3 price tier; cheaper for data read less often | 10 |
| Strands | AWS's open-source agent framework; the Harness is built on it, and the login branch's agent is written in it | 32 |
| Streamable HTTP | the remote MCP transport: JSON-RPC messages over HTTP to one URL | 18 |
| streaming | sending a response in pieces as they are ready | 6 |
| structured output | making the model answer as JSON that matches a given schema | 19 |
| STS | Security Token Service: the AWS service that hands out temporary credentials for a role | 9 |
| stub | a test stand-in that only returns a fixed answer | 26 |
| sub | the permanent id of a person in a Cognito user pool; the actor, the folder, the label key and the Cedar principal on the branch | 31 |
| supervisor (agents) | one agent that receives the task and delegates parts to specialist agents | 16 |
| swarm (agents) | peer agents with no boss that hand work to each other | 16 |
| sync | the Knowledge Base re-reading the bucket; one at a time per data source | 14 |
| system prompt | standing instructions sent with every model call, before the user's words | 19 |
| temperature | the dial for how often a model picks a less likely next token; low for facts | 11 |
| temporary credentials | a key id, secret and session token that expire; what a role hands out | 9 |
| tenant | one customer, company or person whose data must stay apart from everyone else's | 30 |
| tenant label | the `.metadata.json` next to each upload; on the branch its key is the uploader's `sub` and its value `"owner"` | 33 |
| terminal | a window where you type commands | 1 |
| Terraform | the most common cross-cloud infrastructure as code tool; plan, then apply | 8 |
| test | a small program that runs our code with made-up input and checks the output | 3 |
| test double | any stand-in for a real dependency in a test: stub, mock, spy, fake | 26 |
| test pyramid | many fast unit tests, fewer integration tests, very few end-to-end tests | 26 |
| TextDecoderStream | a browser stream that turns bytes into text, holding half-received characters | 7 |
| thread pool | worker threads that run blocking code off the main loop; 40 by default | 5 |
| token | about three quarters of a word; the billing unit for models | 11 |
| token exchange | trading a person's token for a new one aimed at the next service (RFC 8693) | 33 |
| token vault | AgentCore Identity's store of OAuth clients and API keys an agent may borrow, without seeing the secret | 22 |
| tool call | the model asking for a tool by name with JSON arguments; the loop runs it | 16 |
| tool gateway | one front door for many tools: one URL, one auth check, one merged tool menu | 18 |
| tool schema | a tool's menu entry: name, description (what the model reads), input fields | 18 |
| trace | the tree of spans for one request: what happened, in order, and how long each step took | 27 |
| Transaction Search | the CloudWatch setting that stores X-Ray spans in CloudWatch Logs | 27 |
| transpile | translate source into another language's source, like TypeScript into JavaScript | 3 |
| trunk-based development | everyone commits small changes to `main` often, hiding unfinished work behind feature flags | 2 |
| trust policy | the part of a role that says who may assume it | 9 |
| typecheck | an automatic check that types line up | 3 |
| TypeScript | JavaScript with types added; turned into JavaScript before the browser runs it | 3 |
| unit test | a test that calls one function with made-up input | 3 |
| user pool | the Cognito directory that holds the accounts | 31 |
| useState | React's way to hold a value that redraws the component when it changes | 7 |
| uv | the Python package manager we use | 3 |
| uvicorn | the program that runs the FastAPI app and listens on a port | 5 |
| validation | checking input against rules before using it | 5 |
| vector | a list of numbers; here, an embedding | 12 |
| vector database | storage that finds the embeddings nearest to a question's | 10 |
| vector search | finding the chunks whose vectors are closest to the question's | 13 |
| vector store | a database or library that stores vectors and finds the closest ones | 12 |
| version control | a system that keeps every version of a set of files | 2 |
| versioning | S3 keeping every old version of an object | 10 |
| virtual machine | a slice of a physical server that behaves like a whole computer | 8 |
| web framework | a library that handles HTTP plumbing so you write only route functions | 5 |
| WebSocket | a long-lived two-way channel opened from one HTTP request | 4 |
| weights | a model's billions of learned numbers: the model itself, as a file | 11 |
| workload identity | AgentCore Identity's record for one agent or gateway; created automatically; how an agent proves which agent it is | 22 |
| workload identity federation | letting a program outside a cloud (like GitHub Actions) swap its own signed token for short-lived cloud credentials, with no stored key | 22 |
| worktree | a second folder of the same git repository, checked out on another branch | 35 |
| WSGI | the older Python standard for sync servers; Flask and Django under Gunicorn use it | 5 |
| X-Ray | AWS's distributed tracing service | 27 |
| Zep | a memory service that stores chat facts as a knowledge graph that tracks changes over time | 20 |
| zsh | a shell almost identical to bash; the default on macOS and the one used for this project | 1 |
