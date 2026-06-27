FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "mcp[cli]>=1.9.0" "httpx>=0.27.0"

COPY src/mcp_bricks/ /app/mcp_bricks/

VOLUME ["/data"]

CMD ["python", "-m", "mcp_bricks.server"]
