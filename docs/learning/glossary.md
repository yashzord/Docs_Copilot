# Glossary

Every new word, one line, plain meaning. Alphabetical. Add as you go.

| Word | Plain meaning | Track |
|---|---|---|
| access key | username + password pair for programs to call AWS | aws |
| API | a program other programs talk to over HTTP | web |
| App Router | Next.js's way of turning folders into URLs | web |
| async def | a function that says when it is waiting, so the server can serve others meanwhile | web |
| BFF | backend for frontend: a server route the page calls, which calls the real API | web |
| blocking | a call that holds the thread until it finishes (boto3 does this) | web |
| body | the data inside a request or response, JSON for us | web |
| BotoCoreError | boto3 error: never got a proper answer from AWS (network, config) | aws |
| budget | email alarm at a spending threshold, not a cap | aws |
| build system | the tool that turns code into an installable package. Our backend has none: it is run, not installed | tooling |
| CI | continuous integration: a robot runs lint, typecheck, tests on every push | tooling |
| client component | a React component that runs in the browser; the file starts with `"use client"` | web |
| ClientError | boto3 error: AWS answered, and the answer was an error | aws |
| commit | one saved snapshot of the repo | tooling |
| concurrency | many tasks in progress at once, taking turns. Threads waiting on the network give us this | web |
| context window | max tokens a model can hold in one call, everything included | ai |
| Converse API | Bedrock's chat API with one request shape for every model | aws |
| CORS | the browser's rules for calling a different address than the page came from | web |
| dependency | a package our code needs to run | tooling |
| dependency (FastAPI) | a function FastAPI runs before the endpoint, via `Depends(...)` | web |
| dependency override | swapping a FastAPI dependency for another, used in tests | web |
| dev dependency | a tool needed to check the code, never shipped (ruff, pytest) | tooling |
| devDependencies | npm's list of tools needed only to check or build the code | tooling |
| embedding model | outputs a list of numbers (a vector), not text. Used for search | ai |
| endpoint | one URL path + method the server answers, e.g. `POST /v1/chat` | web |
| ESLint | the linter for JavaScript and TypeScript | tooling |
| eval set | fixed list of questions with known good answers, used to score models and RAG | ai |
| event loop | the main thread's to-do loop in an async server: take a request, send a piece, repeat, never wait | web |
| event stream | a response that arrives as a series of small events | web |
| fake | a stand-in object used in tests instead of the real thing | tooling |
| FastAPI | Python library for building API servers | web |
| fixture | a pytest setup function that runs around tests | tooling |
| functional update | `setX(prev => ...)`: compute new state from the latest state | web |
| GIL | Python's lock: one thread runs Python code at a time, but a thread waiting on the network steps aside | web |
| header | a label on a request or response, e.g. `X-Tenant-Id: dev` | web |
| HTTP method | the kind of request: GET reads, POST sends data | web |
| IAM | Identity and Access Management: who can do what in an AWS account | aws |
| IAM user | an identity inside the account with limited powers | aws |
| inference | one call to a model | ai |
| inference profile | a model's ID string on Bedrock. `us.` prefix means any US region may serve it | aws |
| input tokens | what you send: prompt, documents, history | ai |
| lint | automatic check for style mistakes and common bugs (ruff) | tooling |
| lockfile | exact versions of everything installed, so installs repeat | tooling |
| MFA | phone code on top of a password | aws |
| model | text in, text out. Trained on huge amounts of text | ai |
| Next.js | a framework for building web apps with React | web |
| node_modules | installed npm packages. Never committed | tooling |
| npm | Node's package manager | tooling |
| on-demand | pay per token, no commitment | aws |
| output tokens | what comes back. Usually 4 to 5x the price of input | ai |
| package | reusable published code, e.g. `fastapi` | tooling |
| package manager | downloads and installs packages. Ours is uv | tooling |
| package-lock.json | exact npm versions, like `uv.lock`. Committed | tooling |
| package.json | the frontend's list of packages and scripts, like `pyproject.toml` | tooling |
| parallelism | many tasks executing at the same instant on different CPU cores. The GIL blocks this for Python code | web |
| parametrize | run one test many times with different inputs | tooling |
| policy | JSON list of what an AWS identity may do | aws |
| process | one running program with its own memory. uvicorn is one process | web |
| profile | a named set of AWS credentials saved on the laptop | aws |
| proxy | a server that forwards requests to another server | web |
| Pydantic | library that checks data against typed classes | web |
| RAG | retrieval-augmented generation: find relevant document chunks, hand them to the model, answer with citations | ai |
| React | a library for building UIs out of components | web |
| region | which group of AWS data centers a thing lives in | aws |
| remote | a copy of the repo elsewhere, usually GitHub, named `origin` | tooling |
| retry | trying again automatically after a temporary failure | aws |
| root user | the AWS account owner login. Owner tasks only | aws |
| route | same as endpoint | web |
| route handler | a `route.ts` file in Next.js: an API endpoint, not a page | web |
| server component | a React component that runs on the server. The default in the App Router | web |
| SSE | Server-Sent Events: plain-text events over one long HTTP response | web |
| static page | built once at build time and served as a file | web |
| status code | the server's one-number verdict: 200 ok, 4xx caller's fault, 5xx server's fault | web |
| streaming | sending a response in pieces as they are ready | web |
| Tailwind | styling with class names in the markup, e.g. `bg-indigo-600` | tooling |
| TextDecoderStream | browser tool that turns a stream of bytes into text, safely across chunks | web |
| thread | a line of work inside a process. Threads in one process share memory | web |
| thread pool | a set of worker threads that run blocking code off the main loop. 40 by default in FastAPI | web |
| token | about three quarters of a word. The billing unit for models | ai |
| type stripping | Node removing TypeScript types so it can run a `.ts` file directly | tooling |
| type stubs | a package that describes another library's types to mypy | tooling |
| typecheck | automatic check that types line up (mypy) | tooling |
| useEffect | React: run code after the screen updates, e.g. scroll to the bottom | web |
| useState | React: a value that re-draws the component when it changes | web |
| uvicorn | the server program that runs a FastAPI app | web |
| validation | checking input against rules before using it | web |
| venv | a private folder of installed packages for one project | tooling |
| workspace | several Python packages sharing one venv and one lockfile. Not used yet | tooling |
