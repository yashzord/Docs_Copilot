# AWS track

One section per service or concept. Added as the project meets them.

```
1. What AWS is                    D1
2. Account, root, IAM, keys       D1
3. Regions                        D1
4. Budgets                        D1
5. Bedrock                        D1
   5.5 Converse API and its stream
   5.6 When Bedrock says no (errors)
   5.7 Retries
   5.8 Where credentials come from
6. S3                             D2
7. Bedrock Knowledge Bases        D2, D3
8. Neptune Analytics and the cost clock   D4
9. Free tier, corrected           D2
10. AgentCore                     D2 onward
   10.1 the pieces  10.2 Harness  10.3 Gateway  10.4 Memory  10.5 permissions  10.6 what stays ours
(next: Cognito + Identity, Neptune, Runtime, Terraform, CloudWatch)
```

---

## 1. What AWS is

Amazon rents out computers, storage, and services by the hour or by the
request. Instead of buying a server, you borrow one and pay for what you
use.

```
your laptop                    AWS (Amazon's data centers)
  code you write   --calls-->    AI models (Bedrock)
                                 databases, file storage, servers...
                                 bill at the end of the month
```

---

## 2. Account, root, IAM, keys

Everything fits one picture:

```mermaid
flowchart TB
    A[AWS account<br/>the house] --> R[Root user<br/>the owner's master key]
    A --> U[IAM user 'yashubitra'<br/>a key card for daily work]
    U --> P[Policy 'bedrock-dev'<br/>which doors the card opens]
    U --> K[Access key<br/>the card, in a form programs can use]
    A --> B[Budget<br/>smoke alarm for spending]
```

### 2.1 Root user

The email and password the account was created with. Can do anything,
including delete the account or change the card.

**Rule:** root only for owner tasks: MFA, budget, first IAM user. Then
stop using it. If root leaks, someone owns the account. If an IAM key
leaks, they can only do what its policy allows.

### 2.2 IAM user

IAM = Identity and Access Management: the part of AWS that decides who can
do what. An IAM user is a second identity with no powers by default. You
grant exactly what it needs.

Ours: `yashubitra`, no console password, used only from code and terminal.

### 2.3 Policy

A JSON list of allowed actions. Ours, named `bedrock-dev`:

```
bedrock:InvokeModel                    call an AI model
bedrock:InvokeModelWithResponseStream  same, words stream back one by one
bedrock:ListFoundationModels           see which models exist
bedrock:ListInferenceProfiles          see their IDs
budgets:ViewBudget                     read the budget, not change it
```

Nothing creates or deletes. Worst case for a leaked key: a Bedrock bill,
which the budget alarm catches.

### 2.4 Access key and profile

An access key is a username and password for programs:

```
Access key ID       like a username, starts with AKIA...
Secret access key   like a password, shown once
```

`aws configure --profile docs-copilot-dev` stores them in
`~/.aws/credentials` under a **profile** name. Every AWS call the code
makes sends them; AWS finds the user, checks the policy, allows or refuses.

Profile name and IAM username do not need to match.

**Rules:** never paste keys into chat, git, or screenshots. If one leaks,
delete it in IAM and make a new one. One minute.

### 2.4a Inline vs managed policies

A policy can live in two places:

```
inline policy     written directly on one user or role. All inline policies on a
                  user together may be at most 2,048 bytes.
managed policy    a separate object with its own name. Up to 6,144 bytes, attachable
                  to many users and roles. AWS ships some ("AWS managed", e.g.
                  BedrockAgentCoreFullAccess); you can make your own ("customer managed").
```

We hit the 2,048-byte wall on 2026-09-10: the third inline policy was
refused with "Maximum policy size of 2048 bytes exceeded". The fix was to
create it as a customer managed policy and attach it, which is the better
habit anyway: one definition, reused wherever it is needed.

The dev user now carries four:

| Policy | Kind | Grants |
|---|---|---|
| `bedrock-dev` | inline | invoke models, list them, read the budget |
| `kb-dev` | inline | Knowledge Base use, one S3 bucket |
| `BedrockAgentCoreFullAccess` | AWS managed | everything in AgentCore |
| `agentcore-setup` | customer managed | create `AgentCore*` roles and stacks, read logs |

### 2.4b Reading a permission error

Every AWS denial names the exact missing action and the exact resource:

```
User: ...user/yashubitra is not authorized to perform: iam:CreatePolicy
on resource: policy AmazonBedrockCloudWatchPolicyForKnowledgeBase_mq0oz
```

That line is the whole diagnosis: add `iam:CreatePolicy` on policies named
like that, nothing more. Three such walls appeared while creating the
Knowledge Base on 2026-09-10 (a role name pattern, a policy name pattern,
then `bedrock:CreateKnowledgeBase`). Each was fixed by reading the line.

After the third, the AWS managed `AmazonBedrockFullAccess` policy was
attached instead of adding actions one by one. The tradeoff, written down:
the dev key can now do anything in Bedrock (worst case, a model bill the
$30 alarm catches), in exchange for no more setup walls in that service.

Then the decision was made to stop: on a sandbox account that one person
controls, the dev user got `AdministratorAccess`, the same power as root
minus account closure and billing changes. What that trades away: a leaked
laptop key is now the whole account, not just a model bill. What it buys:
no more setup walls. The least-privilege policies stay in `infra/iam/` as
the shape a shared account would use.

Proof the earlier fix worked: the bucket checks that were denied minutes earlier
(`s3:GetBucketLocation` and friends) now answer. What still gets denied:
the user reading its own policy list (`iam:ListAttachedUserPolicies`),
because nothing grants it. That is fine; the console shows it.

### 2.5 MFA

A phone code on top of the password. On for root, no exceptions.

---

## 3. Regions

Groups of data centers:

```
us-east-1    N. Virginia
us-west-2    Oregon        <- ours
eu-central-1 Frankfurt
```

Most things live in one region and are invisible from others. Some
services are global (IAM, budgets).

We use **us-west-2** for everything. Two features needed later (Bedrock
rerank, AgentCore) live there. Picking once avoids moving later.

**Gotcha:** the console remembers the last region you looked at. Check the
top right before creating anything. IAM shows "Global", that is normal.

---

## 4. Budgets

An email alarm, not a cap. AWS emails when the month's bill crosses a
percentage of the number you set. It does not stop anything.

Ours: $30 a month, alerts at 50% and 80%. Created before the first paid
call.

---

## 5. Bedrock

Amazon's AI model service. One API, many models (Claude, Nova, Llama,
others). Pay per token. Which model and why: `ai.md` section 2.

Not to be confused with **Bedrock AgentCore**, a separate console for
hosting agents. That is D6.

Also not to be confused with **Bedrock-mantle**, a second console and
endpoint for OpenAI-style and Anthropic-style API calls with API keys. We
use the original **Bedrock-runtime** console: IAM keys, the Converse API,
cross-region inference profiles. The link between them is at the bottom
left of either console.

### 5.1 Model access

Some models need a one-time "request access" per account, from the model's
page in **Model catalog**. Usually instant. Anthropic models may ask for a
short use-case form the first time.

### 5.2 Inference profile IDs

Every model has an ID string. Ones starting with `global.` or `us.` are
cross-region inference profiles: AWS may run the request in another region
for better availability. `global.` = anywhere, list price. `us.` = US only,
about 10% more on Claude. Copy from console, **Inference profiles**, into
`.env`. Never type from memory.

### 5.3 How the code uses all of this

```mermaid
sequenceDiagram
    participant C as backend/app (your code)
    participant F as ~/.aws/credentials
    participant B as Bedrock (us-west-2)
    C->>F: read profile docs-copilot-dev
    C->>B: InvokeModelWithResponseStream + access key + model ID
    B->>B: which user? policy allows? model access granted?
    B-->>C: answer, streamed word by word
    B->>B: add tokens to the bill, budget alarm watches the total
```

### 5.4 D1 setup checklist

```
[x] account created
[x] MFA on root
[x] budget $30
[x] IAM user yashubitra, no console access
[x] policy bedrock-dev on that user
[x] access key, "Command Line Interface"
[x] aws configure --profile docs-copilot-dev
[x] model access for Llama 4 Maverick, region us-west-2 (tested in Playground)
[x] its us. ID into .env
```

### 5.5 The Converse API and its stream

Converse is Bedrock's model-agnostic chat API: one request shape for every
model. `converse_stream` is the streaming version.

What we send:

```python
client.converse_stream(
    modelId="us.meta.llama4-maverick-17b-instruct-v1:0",
    messages=[{"role": "user", "content": [{"text": "hi"}]}],
    inferenceConfig={"maxTokens": 1024},   # caps answer length, so caps cost
)
```

Note `content` is a **list** of blocks. Text today; images and documents
are other block types later.

What comes back is a stream of events, one dict each:

| Event | Contains | We use it? |
|---|---|---|
| `messageStart` | role `assistant` | no |
| `contentBlockDelta` | `delta.text`: the next piece of the answer | yes, becomes `event: delta` |
| `contentBlockStop` | end of a block | no |
| `messageStop` | `stopReason`: `end_turn`, `max_tokens`, ... | not yet |
| `metadata` | `usage` (tokens in and out) and `metrics.latencyMs` | yes, becomes `event: usage` and a log line |

The code for this lives in `backend/app/llm.py`.

Docs: https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse_stream.html

### 5.6 When Bedrock says no

boto3 raises one of two kinds of error:

| Kind | Means | Examples |
|---|---|---|
| `ClientError` | AWS answered, and the answer was an error | `ThrottlingException`, `AccessDeniedException`, `ValidationException` |
| `BotoCoreError` | never got a proper answer from AWS | no network, timeout, bad local config |

`err.response["Error"]["Code"]` gives the error name.
`err.response["ResponseMetadata"]["RequestId"]` gives an id AWS support can
look up. We log both. We never pass AWS's message text to the caller.

How we answer the caller:

| Bedrock said | Caller gets |
|---|---|
| `ThrottlingException`, `ServiceUnavailableException`, `ModelNotReadyException` | 503 + `Retry-After: 5` |
| any other error, before streaming | 502 |
| any error after streaming started | `event: error` inside the stream (web.md section 5) |

A doc summary fetched while building this claimed `ClientError` is a
subclass of `BotoCoreError`. Checking the installed code showed it is not.
Lesson: when a detail matters, check the source, not a summary.

Docs: https://docs.aws.amazon.com/boto3/latest/guide/error-handling.html

### 5.7 Retries

A retry = trying again automatically after a temporary failure, with a
growing pause between tries.

boto3 has three retry modes. The default is still `legacy`. We set
`standard`: up to 3 attempts in total, and it retries throttling and
network blips.

```python
Config(retries={"mode": "standard"})
```

Retries only cover **opening** the stream. A stream that breaks halfway is
not retried: the user already saw part of an answer.

Docs: https://docs.aws.amazon.com/boto3/latest/guide/retries.html

### 5.8 Where the code's credentials come from

```
AWS_PROFILE set (our .env)   ->  ~/.aws/credentials, profile docs-copilot-dev
AWS_PROFILE not set          ->  boto3's default chain: env vars, then the
                                 container's role when running on AWS (D8)
```

The server log shows which one it used:
`Found credentials in shared credentials file: ~/.aws/credentials`.

---

## 6. S3

Object storage: a giant key-value store for files. A **bucket** is a
top-level container with a globally unique name; an **object** is one file
under a **key** that looks like a path.

```
bucket: docs-copilot-901708383582
  key:  tenants/dev/handbook.pdf                  the file
  key:  tenants/dev/handbook.pdf.metadata.json    its labels (section 7.3)
```

Things that matter for us:

- **Region:** the bucket lives in us-west-2, same as the Knowledge Base. Must match.
- **Private by default:** "Block public access" stays on. Only our IAM user and the KB's service role can read it.
- **No folders, really:** the slashes in a key are just characters. Listing "tenants/dev/" is a prefix search.
- **Cost:** about $0.023 per GB per month, plus fractions of a cent per request. Our corpus is megabytes.
- **Why keep files here at all:** citations link back to the original; the KB can be rebuilt from the bucket at any time; the KB reads *from* S3, it does not accept uploads directly.

### 6.1 Every option on the "Create bucket" form, and what we picked

Created 2026-09-10 as `docs-copilot-901708383582`.

| Option | Choices | We picked | Why |
|---|---|---|---|
| Bucket type | General purpose / Directory | General purpose | Directory buckets are a special low-latency type in one availability zone. The Knowledge Base only supports general purpose |
| Bucket namespace | Global / Account Regional | Global | names in the global namespace must be unique across all of AWS (hence the account id in ours). The newer account-regional kind has a different address format, and the Knowledge Base connector and our IAM policies use the classic `arn:aws:s3:::name` form |
| Object Ownership | ACLs disabled / ACLs enabled | ACLs disabled | ACLs are the old per-object permission lists. Disabled means "only IAM policies decide access", one system instead of two |
| Block all public access | on / off | on | nothing in this bucket is ever meant to be reachable from the internet |
| Bucket Versioning | Disable / Enable | Disable | versioning keeps every old copy of every object (protects against accidental overwrites, costs storage). Re-uploading a document is fine for us |
| Tags | optional | none | labels for cost reports. One project, one account: nothing to separate |
| Default encryption | SSE-S3 / SSE-KMS / DSSE-KMS | SSE-S3 | every object is encrypted at rest either way. SSE-S3 uses keys AWS manages, free. KMS uses a key you manage and audit, with a per-request fee |
| Bucket Key | Enable / Disable | Enable (default) | only matters for KMS; it caches the key to cut KMS calls. Harmless with SSE-S3 |

**Denied by default, proven:** right after creating the bucket, the dev
user could not even ask which region it was in (`AccessDenied` on
`s3:GetBucketLocation`). Creating something as root does not grant the
IAM user anything. The `kb-dev` policy (`infra/iam/kb-dev.json`) adds
exactly the actions needed, on exactly this bucket.

---

## 7. Bedrock Knowledge Bases

A managed RAG service. You give it documents; it runs the whole pipeline
from `ai.md` section 4 and answers `Retrieve` calls with the best chunks.

### 7.1 Managed vs customer-managed

| | Managed KB (ours) | Customer-managed KB |
|---|---|---|
| vector store | AWS's, invisible | you pick: S3 Vectors, OpenSearch, Aurora, Neptune... |
| embedding model | AWS's, or a Bedrock one | you pick |
| search | always hybrid | depends on the store |
| reranker | built in, free (managed embeddings only) | via the Rerank API, paid |
| parser | built in, handles images too | default, or a model |
| chunking | default or fixed-size | also semantic, hierarchical |
| data sources | S3, Web Crawler, Confluence, SharePoint, Drive, ... | S3, custom |
| GraphRAG | no | yes, on Neptune Analytics |
| price | $5 per GB of raw data per month + $1 per 1,000 Retrieve calls | pay for the store, embeddings, rerank separately |

So we run **two**: a managed KB for documents (D2), and a small
customer-managed KB for the graph (D4).

### 7.1a Every option on the "Create Managed Knowledge Base" form

Created 2026-09-10 as `docs-copilot-kb` by the IAM user (a root user is
not allowed to create one).

| Section | Option | We picked | What it means |
|---|---|---|---|
| KB details | Embeddings model | Managed | AWS runs the embedding model (ai.md 4.3) at no extra cost. Required for the free built-in reranker. The alternative lets you pick Titan or Cohere and pay per token |
| | IAM permissions | Create and use a new service role | a **service role** is the identity the Knowledge Base itself uses to read your bucket and call models. The console wrote its permissions |
| | KMS key | default (AWS owned) | the vector store is encrypted either way; your own key only matters when you must control and audit the key |
| Data source | Type | Amazon S3 | where documents come from. Web Crawler is the one for URLs, added later as a second data source |
| | Location / S3 URI | this account, `s3://docs-copilot-901708383582` | the bucket it reads on every sync |
| | Crawl ACLs | Disable | ACL crawling copies per-document permissions from sources like SharePoint. S3 has none; our tenant wall is the metadata file |
| | Parsing strategy | Managed parser | PDF, Word, HTML to text (ai.md 4.1), images included |
| | Chunking strategy | Default | ~300-token chunks at sentence boundaries (ai.md 4.2). **Cannot be changed later**; comparing strategies means a second data source |
| | Sync schedule | On-demand | a sync (ingestion job) runs only when asked. Our API asks after each upload |
| | Prefix and file filters | none | would limit syncing to certain folders or extensions |
| | Log deliveries | none | sync logs to CloudWatch; useful when a file fails to index, not now |
| Advanced | Content indexing | Default (text) | advanced indexing also reads images, audio, video, at extra cost per file |
| | Max file size | default | |
| | Document deletion safeguard | Off | when on, a sync that would delete many chunks skips deletion, to survive an accidentally emptied bucket. Small corpus: we want deletions to apply |

### 7.2 The pieces

```mermaid
flowchart LR
    U[our API] -->|1 upload file + metadata| S[(S3 bucket)]
    U -->|2 StartIngestionJob| KB[Knowledge Base]
    KB -->|3 reads| S
    KB -->|4 parse, chunk, embed, index| ST[(managed store)]
    U -->|5 Retrieve question + tenant filter| KB
    KB -->|6 top chunks + sources| U
    R[service role] -.lets the KB read S3 and call models.-> KB
```

- **Knowledge base:** the top-level object. Has an ID.
- **Data source:** where documents come from (one S3 bucket, or one web crawl). Chunking is set per data source and cannot be changed after; to compare strategies you make two data sources.
- **Ingestion job:** the background run that reads new, changed, and deleted files and updates the index. Started by `StartIngestionJob`, finished minutes later. This is why we do not need our own queue and worker.
- **Service role:** an IAM role the KB assumes to read your bucket and call Bedrock models. The console creates it for you.

### 7.3 Tenant wall: metadata files

Next to each uploaded file goes a tiny JSON:

```
handbook.pdf.metadata.json
{ "metadataAttributes": { "tenant_id": "dev", "source": "upload" } }
```

Every `Retrieve` call carries a filter: `tenant_id equals <the caller's
tenant>`. A tenant can never see another tenant's chunks, however the
question is phrased. Our API adds the file, the metadata file, and the
filter; nobody else ever sees `tenant_id`.

### 7.4 Retrieve

One call, one question, top chunks back:

```
Retrieve(knowledgeBaseId, retrievalQuery="...", retrievalConfiguration:
  managedSearchConfiguration:
    rerankingModelType: MANAGED | CUSTOM | NONE      <- the D3 toggle
    filter: tenant_id equals "dev")
-> results: [ {content.text, location.s3Location.uri, score, metadata}, ... ]
```

We then build the prompt ourselves and stream the answer with Llama
through the Converse API from D1. The KB also offers
`RetrieveAndGenerate`, which writes the answer for you; we skip it because
our agents need the raw chunks, and generation is already ours.

### 7.4a Verified end to end, before any code

2026-09-10, by hand from the CLI:

```
upload      tenants/dev/README.md  +  README.md.metadata.json {tenant_id: dev}
sync        StartIngestionJob -> 2.5 minutes -> COMPLETE, 1 document indexed, 0 failed
retrieve    via the gateway tool docs___Retrieve("why was Neptune Analytics dropped?")
            -> 5 passages, best score 0.63, each with the S3 source URL and tenant_id=dev
            -> passage [2] is the README's decision table with the Neptune row
tenant wall Retrieve with filter tenant_id=dev   -> 3 passages
            Retrieve with filter tenant_id=other -> 0 passages
```

So the whole path (bucket, metadata, sync, index, hybrid search, rerank,
gateway, filter) works with zero lines of our code. What our code adds is
the upload endpoint, the sync trigger, and the UI.

### 7.5 Permissions our user needs

The dev user gets a second inline policy: `bedrock:Retrieve`,
`bedrock:StartIngestionJob`, `bedrock:GetIngestionJob`, and S3 read/write
on the one bucket. The KB's own service role is separate; the console
creates it.

---

## 8. Neptune Analytics and the cost clock

Neptune Analytics is AWS's graph database engine. Bedrock GraphRAG stores
the knowledge graph in it. Unlike everything else in this project, it
**bills by the hour whether or not it is used**.

```
size:    32 m-NCU minimum (an m-NCU is 1 GB of memory + compute for one hour)
price:   $0.1098 per m-NCU-hour  ->  $3.51 per hour  ->  $84 per day running
paused:  10% of that, about $8 per day
deleted: $0
```

The rule for this project:

```
D4 starts  -> create graph KB, ingest, test        (a few hours, ~$10)
between    -> PAUSE the graph                      (~$8/day)
demo day   -> unpause, demo, then DELETE the KB and the graph
```

Deleting the knowledge base does **not** delete the graph. Both must be
deleted, KB first. The $30 budget alarm is the safety net if either is
forgotten.

Source: https://aws.amazon.com/neptune/pricing/ and
https://aws.amazon.com/about-aws/whats-new/2024/07/amazon-neptune-analytics-smaller-capacity-units

---

## 9. Free tier, corrected

Earlier notes said this account would get 12 months of free OpenSearch and
RDS hours. Wrong: accounts created after 2025-07-15 get **credits** instead
($100 at sign-up, up to $100 more for trying core services), valid up to
12 months, and no 12-month free service hours. Everything we use draws
from those credits, which is another reason to prefer services that bill
per request (Knowledge Base, S3, Bedrock) over ones that bill per hour
(Neptune, OpenSearch domains, RDS).
Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html

---

## 10. AgentCore

Bedrock is where models live. **AgentCore** is where agents live: the
loop, the tools, the memory, the login, the tracing, all as managed
services. Every piece is independent; we use most of them.

### 10.1 The pieces

| Piece | Job | We use it in |
|---|---|---|
| **Harness** | a managed agent: model + instructions + tools + memory as config; AWS runs the loop | D2 |
| **Gateway** | turns APIs, Lambda functions, Knowledge Bases and other agents into MCP tools, with auth and policy | D2 |
| **Memory** | short-term (conversations) and long-term (extracted facts) per user | D2, D5 |
| **Identity** | login with Cognito or others; a token vault so agents can act on a user's behalf | D3, D7 |
| **Code Interpreter** | a sandbox where the agent runs Python safely | D5 |
| **Browser** | a managed browser the agent drives to read web pages | D5, D6 |
| **Runtime** | serverless hosting for agent code you write (Strands, LangGraph, anything) | D6 |
| **Observability** | traces of every step, in CloudWatch | D7 |
| **Evaluations** | scores agent sessions and RAG answers with a judge model | D7 |
| **Policy** | rules (Cedar) checked on every tool call | D7 |
| Registry, Optimization, Payments | catalog, prompt tuning, paid tools | not planned |

Pricing is per use, no hourly minimum (unlike Neptune): Runtime by active
CPU-seconds, Memory per event and record, Gateway per call.

### 10.2 Harness

The assistant is a Harness. What we declare:

```
model:        a Bedrock model id (default global.anthropic.claude-sonnet-4-6; any Bedrock model
              works, and it can be overridden per call, so comparing models is one flag)
instructions: the system prompt
tools:        Gateway ARN, Code Interpreter, Browser, remote MCP servers, inline functions
memory:       managed, with strategies (SEMANTIC, SUMMARIZATION, USER_PREFERENCE)
limits:       maxIterations, timeoutSeconds, maxTokens
truncation:   sliding_window or summarization
```

What AWS does: runs each session in its own micro-VM with a filesystem
and shell, calls the model, runs the tools, writes memory, traces
everything, and streams the result back. The stream has the same event
shape as the Converse API from D1 (`contentBlockDelta`, `messageStop`,
`metadata`), plus `toolUse` blocks, so the UI can show "calling
Retrieve..." live.

Invoking it is one call, `InvokeHarness`, with a session id (at least 33
characters) and an `actorId` (the user). Same session id = same
conversation.

Not possible in a Harness: a workflow with explicit steps, or several
agents coordinating. For that, code on Runtime (D6).

### 10.2a Every option on the "Create Harness" form

Created 2026-09-11 as `docs_copilot_assistant` with **Advanced create**
(Quick create asks only for a name and uses defaults). The name cannot be
changed later and allows letters, digits and underscores, no dashes.

| Section | Option | We picked | What it means |
|---|---|---|---|
| Model | Model source | Bedrock | the other choices call LiteLLM, OpenAI or Gemini directly with your own keys |
| | API source | Bedrock (Converse) | Mantle is the OpenAI-style API. Converse is needed for Guardrails later |
| | Model | gpt-oss-120b | first Llama 4 Maverick, which failed: no tool use while streaming (ai.md 2.7) |
| | System prompt | `backend/prompts/assistant.md` | the agent's standing instructions: search first, cite `[1]`, admit gaps |
| | Parameters | empty | temperature and max tokens stay at the model's defaults |
| Memory | Enable, create new (managed by Harness) | on | the harness creates an AgentCore Memory and saves every message to it; takes 3 to 5 minutes |
| | Strategies | Summarization | long-term memory: a running summary per conversation. Semantic (facts) and user preference come in D5 |
| | Short-term expiration | 30 days | raw messages are deleted after this |
| Tools | Gateway | `docs-copilot-gw`, outbound auth IAM | the agent's tools come from the gateway over MCP |
| | Browser, Code interpreter | off | D5 |
| | Remote MCP server, Custom functions | none | tools hosted elsewhere, or run by our own app |
| Skills | | none | bundles of files and scripts the agent can use |
| Advanced | Filesystem | none | persistent storage between sessions |
| | Network | Public | VPC only when the agent must reach private resources |
| | Custom environment | empty | our own container image, for extra software |
| | Idle session timeout | 15 minutes | a quiet session's machine is stopped, so it stops costing |
| | Max lifetime | 1 hour | the longest a session's machine may live |
| | Truncation | Sliding window, 30 messages | only the last 30 messages go to the model each turn |
| | Allowed tools | only the gateway's tools | removes the built-in shell and file tools, which a document assistant must not have |
| | Max iterations / timeout / max tokens | 10 / 5 min / 2048 | caps on one answer: loop turns, time, and length |
| Inbound Auth | | IAM | who may call the harness: any AWS identity with permission. JWT login comes in D3 |
| Permissions | | create default role | the harness's own identity. It gets model access, the gateway, its memory, and (by default) Browser, Code Interpreter and file system rights we do not use yet |

Verified after creation (CLI `get-harness`): model, prompt, the gateway tool,
allowed tools `@<gateway>`, memory `docs_copilot_assistant-6aIbceHbw1`.

### 10.3 Gateway

An MCP server AWS runs for you. You add **targets**; each becomes tools:

```mermaid
flowchart LR
    H[Harness<br/>MCP client] -->|IAM-signed MCP calls| G[Gateway]
    G --> K[managed Knowledge Base<br/>tools: Retrieve, AgenticRetrieveStream]
    G --> L[Lambda function<br/>e.g. graph search on the GraphRAG KB]
    G --> R[Runtime agent<br/>e.g. research agent]
    P[Policy engine] -.checks every call.-> G
```

Inbound auth (who may call the gateway): **IAM** to start, a Cognito JWT
from D3. Outbound auth (how the gateway reaches each target): its own
service role. The gateway can also hide or fix tool parameters, so the
agent sees a simpler tool than the underlying API.

The Knowledge Base target exposes the same `Retrieve` we studied in
section 7.4, and `AgenticRetrieveStream`, a multi-step retrieval that
plans sub-questions itself. Only managed Knowledge Bases can be targets,
so the GraphRAG one (customer-managed) goes behind a small Lambda.

By default the agent sees only `retrievalQuery.text`; everything else
(`numberOfResults`, reranking, the metadata `filter`) is fixed by the
administrator on the target. That is good for safety and bad for
multi-tenancy: the filter is per target, not per caller. So the tenant
wall in D3 will be either one target per tenant, or the Knowledge Base's
own access-control mode with a per-user `userContext`. Decided in D3, not
now.

### 10.3a Every option on the "Create gateway" form

Created 2026-09-10 as `docs-copilot-gw`. IDs live in `backend/.env.example`.

| Step | Option | We picked | What it means |
|---|---|---|---|
| 1 details | Semantic search | off | lets an agent search a big tool catalog by meaning, billed per search. We have three tools |
| | Exception level debugging | off | verbose AWS-side logs |
| | Response streaming | on | a tool may stream partial results (the KB's agentic tool does) |
| | Sessions | off | stateful MCP sessions; our calls are one-shot |
| | MCP version | 2026-07-28 (and 2025-11-25) | the protocol versions the gateway speaks; fixed at creation. A client names one in the `MCP-Protocol-Version` header. Found while testing: 2026-07-28 also requires a `_meta` field in every call; 2025-11-25 does not. The harness handles this itself; it matters only for hand-made calls |
| | Interceptor Lambdas | none | your own code to rewrite requests or responses |
| | IAM permissions | create default role | the gateway's **service role**, used to reach targets |
| | Policy engine | none | rules on tool calls, D7 |
| | WAF | off | a web firewall, about $5 a month; our gateway needs AWS credentials to call anyway |
| 2 inbound identity | Inbound auth | AWS IAM | who may call: any AWS identity with `InvokeGateway`. JWT (a login token) comes in D3. "No authorization" would make it public. "Authenticate only" checks the signature but not permissions |
| 3 target | Protocol | MCP target | the other kinds: inference (call a model), agent (front another agent, D6), custom (raw HTTP) |
| | Name | `docs` | becomes the tool prefix: `docs___Retrieve` |
| | Passthrough | off (aggregated) | the gateway is the MCP server and merges all targets into one tool list; passthrough would make it a proxy to one server |
| | Target type | Connectors, Knowledge Bases | pre-built target for a managed KB |
| | Retrieval type | Standard | exposes `Retrieve` (one hybrid search per call). Agentic would expose `AgenticRetrieveStream`, multi-step planning at $4 per 1,000 calls, overlapping the harness |
| | Source chunks | 5 | passages returned per search; tuned by the eval in D7 |
| | Manual filters | none | a fixed metadata filter, e.g. `tenant_id = dev`, per target. The multi-tenant question for D3 |
| | Model generated filters | off | a model guesses filters from the question, ~2,000 extra tokens per call |
| | Guardrail | none | D7 |
| | Reranking | Default | the free managed reranker (ai.md 4.6). Console default is off; ours is on |
| | Agent overrides | none | would let the model change chunk count or pass a user context |
| | Outbound auth | IAM role | how the gateway authenticates to the KB; the only option for this connector |

### 10.3b Verified: the gateway as an MCP server

Called by hand on 2026-09-10 with a signed request (curl can sign with
SigV4 given the access key), before any of our code existed:

```
tools/list  ->  one tool: docs___Retrieve
                argument: retrievalQuery.text (string)
tools/call docs___Retrieve {"retrievalQuery": {"text": "vacation days"}}
            ->  {"retrievalResults": []}        (the bucket was still empty)
```

That is the whole contract the harness will use. The tool name is the
target name, three underscores, the tool.

### 10.4 Memory

A Memory resource holds **events** (messages, tool calls) grouped by
`actorId` (the user) and `sessionId` (one conversation).

```
actor user-123
  session 2026-09-11-a   events: user msg, assistant msg, tool call, ...
  session 2026-09-11-b   events: ...
```

`ListSessions(actorId)` gives the sidebar; `ListEvents(actorId,
sessionId)` gives one conversation back. Sessions carry a creation time,
not a title, so the title is the first user message.

Long-term memory is a **strategy** on the resource: after each session,
AWS extracts facts (SEMANTIC), a running summary (SUMMARIZATION), or
preferences (USER_PREFERENCE) into records, which the harness searches at
the start of the next session. Events expire after a configurable number
of days.

### 10.5 Permissions

Three identities are involved, and mixing them up is the usual failure:

| Identity | What it is | Needs |
|---|---|---|
| your dev user (`yashubitra`) | you, from the laptop | create and invoke harnesses, gateways, memory; the documented dev path is the AWS managed policy `BedrockAgentCoreFullAccess` plus our `kb-dev` policy |
| harness execution role | the harness acting on its own | invoke Bedrock models, call the Gateway, read and write Memory |
| gateway service role | the gateway reaching its targets | `bedrock:Retrieve` on the Knowledge Base, invoke the Lambda |

The AgentCore CLI and console create the two roles for you, which is
why the dev user also needs permission to create roles whose names start
with `AgentCore` (see `infra/iam/`).

Calling a harness needs two actions at once: `InvokeHarness` on the
harness and `InvokeAgentRuntime` on the runtime underneath it. Reading
the sidebar needs `ListSessions` and `ListEvents` on the memory.

### 10.6 What stays ours

```
Next.js UI            chat, sidebar, citations, tool-call trace
FastAPI (thin)        verify login token -> tenant; upload to S3 + metadata + StartIngestionJob;
                      InvokeHarness and relay the stream; ListSessions / ListEvents for the sidebar
Strands code (D6)     the research agent on Runtime
```

Everything else is configuration of the services above.

---

## Check yourself

1. Why does the IAM user get a policy but root does not need one?
2. Worst thing someone can do with a leaked `bedrock-dev` key?
3. Does the budget stop spending at $30?
4. Why us-west-2 and not whatever the console shows?
5. Where on the laptop do the access keys end up?
6. Which stream event carries the text, and which carries the token counts?
7. What is the difference between `ClientError` and `BotoCoreError`?
8. Why is a stream that breaks halfway not retried?
9. What does the `.metadata.json` file next to an upload do, and who reads it?
10. Why do we not need our own queue and worker with a Knowledge Base?
11. What must be deleted after the demo, and in which order?
12. Which AgentCore piece runs the agent loop, and which one turns the Knowledge Base into a tool?
13. What are the three IAM identities in an AgentCore setup, and what does each need?
