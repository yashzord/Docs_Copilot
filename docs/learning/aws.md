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
(next: S3, SQS, Cognito, OpenSearch, AgentCore, Terraform, ECS Fargate, CloudWatch)
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

## Check yourself

1. Why does the IAM user get a policy but root does not need one?
2. Worst thing someone can do with a leaked `bedrock-dev` key?
3. Does the budget stop spending at $30?
4. Why us-west-2 and not whatever the console shows?
5. Where on the laptop do the access keys end up?
6. Which stream event carries the text, and which carries the token counts?
7. What is the difference between `ClientError` and `BotoCoreError`?
8. Why is a stream that breaks halfway not retried?
