FROM python:3.11-slim

WORKDIR /action

# Pin deps for reproducibility
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the core script, MCP client, and entrypoint
COPY jira_integration_script.py .
COPY mcp_client.py .
COPY entrypoint.sh .

RUN chmod +x /action/entrypoint.sh

ENTRYPOINT ["/action/entrypoint.sh"]
