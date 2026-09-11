# IAM policies for the dev user

**Current state (2026-09-10):** the dev user `yashubitra` has the AWS managed
`AdministratorAccess` policy. Decision: this is a single-person sandbox
account, and three permission walls in a row during setup cost more than
least privilege was buying. Tradeoff accepted and recorded: the laptop's
access key now equals the whole account; if it leaks, delete it in IAM at
once. The budget alarm remains the safety net.

The policies below are the least-privilege shape this project would use on
a shared or production account. They are kept as documentation and were
each attached and verified before the switch.


Attach to the IAM user `yashubitra` (IAM, Users, Add permissions, Create
inline policy, JSON). Each file is one inline policy. Plain words on what
each allows and why are in `docs/learning/aws.md` sections 2 and 10.5.

| Policy | Allows | Why |
|---|---|---|
| `bedrock-dev` (created in D1, in the console) | invoke Bedrock models, list them, read the budget | the D1 chat |
| `kb-dev.json` | Retrieve from Knowledge Bases, start and read ingestion jobs, read and write objects in one S3 bucket, read that bucket's settings | uploads, search, and verifying the bucket from the CLI |
| AWS managed `BedrockAgentCoreFullAccess` | everything in AgentCore, plus pass roles named *BedrockAgentCore* | create and invoke harness, gateway, memory |
| AWS managed `AmazonBedrockFullAccess` | everything in Bedrock, including creating Knowledge Bases | the console creates the KB's service role and policies, which needs Bedrock-wide rights; attached 2026-09-10 after the third permission wall |
| `dev-user-agentcore-setup.json` | create IAM roles named `AgentCore*`, run CloudFormation stacks named `AgentCore-*`, read CloudWatch logs | the AgentCore CLI creates roles and stacks on deploy |

Least privilege, honestly applied: every statement is scoped to names this
project creates, except CloudWatch log reads. On a shared or production
account these would be narrower still.
