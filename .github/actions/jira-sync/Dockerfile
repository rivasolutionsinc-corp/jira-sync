FROM python:3.11-slim

WORKDIR /action

# Pin deps for reproducibility
COPY .github/actions/jira-sync/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the core script and entrypoint
COPY jira_integration_script.py .
COPY .github/actions/jira-sync/entrypoint.sh .

RUN chmod +x /action/entrypoint.sh

ENTRYPOINT ["/action/entrypoint.sh"]
