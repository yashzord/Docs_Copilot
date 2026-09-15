# The agent's container for AgentCore Runtime (docs/course.md lesson 17).
# Built for arm64 by the AgentCore CLI in CodeBuild; run locally with
# `PORT=8081 uv run python src/main.py` instead (lesson 26).
FROM python:3.12-slim

WORKDIR /app
# Pinned dependencies first, so a code change does not reinstall them.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

# Runtime talks to the agent on 8080: POST /invocations, GET /ping.
EXPOSE 8080
CMD ["python", "main.py"]
