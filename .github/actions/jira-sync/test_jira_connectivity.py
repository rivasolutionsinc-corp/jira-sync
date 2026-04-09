#!/usr/bin/env python3
"""Test Jira connectivity by listing issues in a project."""

import requests
import os
import sys

def test_jira_connectivity():
    """Test connection to Jira and list issues."""
    jira_url = os.getenv('JIRA_URL', 'https://cmext.ahrq.gov/jira')
    jira_token = os.getenv('JIRA_TOKEN')
    project_key = os.getenv('PROJECT_KEY', 'CLOUD')

    if not jira_token:
        print('⚠ JIRA_TOKEN not set - skipping Jira connectivity test')
        return 0

    headers = {
        'Authorization': f'Bearer {jira_token}',
        'Content-Type': 'application/json'
    }
    url = f'{jira_url}/rest/api/2/search?jql=project={project_key}&maxResults=5'

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'✓ Successfully connected to Jira')
            print(f'✓ Found {data["total"]} issues in project {project_key}')
            if data['issues']:
                print(f'✓ Sample issues:')
                for issue in data['issues'][:3]:
                    print(f'  - {issue["key"]}: {issue["fields"]["summary"]}')
            return 0
        else:
            print(f'⚠ Jira returned status {response.status_code}')
            print(f'  Response: {response.text[:200]}')
            return 1
    except Exception as e:
        print(f'⚠ Could not connect to Jira: {str(e)}')
        return 1

if __name__ == '__main__':
    sys.exit(test_jira_connectivity())
