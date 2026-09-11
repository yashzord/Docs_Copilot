# IAM policies for the dev user

Attach to the IAM user `yashubitra` (IAM, Users, Add permissions, Create
inline policy, JSON). Each file is one inline policy. Plain words on what
each allows and why are in `docs/learning/aws.md` sections 2 and 10.5.

| Policy | Allows | Why |
|---|---|---|
| `bedrock-dev` (created in D1, in the console) | invoke Bedrock models, list them, read the budget | the D1 chat |
| `kb-dev` (D2, in the console; text in docs/learning/D1.md history) | Retrieve from Knowledge Bases, start and read ingestion jobs, read and write one S3 bucket | uploads and search |
| AWS managed `BedrockAgentCoreFullAccess` | everything in AgentCore, plus pass roles named *BedrockAgentCore* | create and invoke harness, gateway, memory |
| `dev-user-agentcore-setup.json` | create IAM roles named `AgentCore*`, run CloudFormation stacks named `AgentCore-*`, read CloudWatch logs | the AgentCore CLI creates roles and stacks on deploy |

Least privilege, honestly applied: every statement is scoped to names this
project creates, except CloudWatch log reads. On a shared or production
account these would be narrower still.
