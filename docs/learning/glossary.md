# Glossary

Every new word, one line, plain meaning. Alphabetical. Add as you go.

| Word | Plain meaning | Track |
|---|---|---|
| access key | username + password pair for programs to call AWS | aws |
| budget | email alarm at a spending threshold, not a cap | aws |
| CI | continuous integration: a robot runs lint, typecheck, tests on every push | tooling |
| commit | one saved snapshot of the repo | tooling |
| context window | max tokens a model can hold in one call, everything included | ai |
| dependency | a package our code needs to run | tooling |
| embedding model | outputs a list of numbers (a vector), not text. Used for search | ai |
| eval set | fixed list of questions with known good answers, used to score models and RAG | ai |
| IAM | Identity and Access Management: who can do what in an AWS account | aws |
| IAM user | an identity inside the account with limited powers | aws |
| inference | one call to a model | ai |
| inference profile | a model's ID string on Bedrock. `us.` prefix means any US region may serve it | aws |
| input tokens | what you send: prompt, documents, history | ai |
| lint | automatic check for style mistakes and common bugs (ruff) | tooling |
| lockfile | exact versions of everything installed, so installs repeat | tooling |
| MFA | phone code on top of a password | aws |
| model | text in, text out. Trained on huge amounts of text | ai |
| on-demand | pay per token, no commitment | aws |
| output tokens | what comes back. Usually 4 to 5x the price of input | ai |
| package | reusable published code, e.g. `fastapi` | tooling |
| package manager | downloads and installs packages. Ours is uv | tooling |
| policy | JSON list of what an AWS identity may do | aws |
| profile | a named set of AWS credentials saved on the laptop | aws |
| RAG | retrieval-augmented generation: find relevant document chunks, hand them to the model, answer with citations | ai |
| region | which group of AWS data centers a thing lives in | aws |
| remote | a copy of the repo elsewhere, usually GitHub, named `origin` | tooling |
| root user | the AWS account owner login. Owner tasks only | aws |
| token | about three quarters of a word. The billing unit for models | ai |
| typecheck | automatic check that types line up (mypy) | tooling |
| venv | a private folder of installed packages for one project | tooling |
| workspace | several Python packages sharing one venv and one lockfile | tooling |
