import os
import requests
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_latest_workflow_status(repo, workflow_name=None):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    workflows_url = f"https://api.github.com/repos/{repo}/actions/workflows"
    workflows_resp = requests.get(workflows_url, headers=headers)

    if workflows_resp.status_code != 200:
        return f"❌ GitHub API error: {workflows_resp.status_code}\n🔍 Check that the repo `{repo}` exists and is public."

    workflows = workflows_resp.json().get("workflows", [])
    if not workflows:
        return "⚠️ No workflows found in this repo."

    matched = None

    if workflow_name:
        # Normalize .yml/.yaml
        workflow_name = workflow_name.replace(".yml", ".yaml")
        matched = next((wf for wf in workflows if wf["path"].endswith(workflow_name)), None)
        if not matched:
            return f"⚠️ Workflow `{workflow_name}` not found in repo `{repo}`."
    else:
        matched = workflows[0]
        workflow_name = matched["path"].split("/")[-1]  # default for reply

    workflow_id = matched["id"]

    # Get runs
    runs_url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/runs"
    runs_resp = requests.get(runs_url, headers=headers)

    if runs_resp.status_code != 200:
        return f"❌ Failed to get workflow runs: {runs_resp.status_code}"

    runs = runs_resp.json().get("workflow_runs", [])
    if not runs:
        return f"⚠️ Workflow `{workflow_name}` has no runs yet."

    latest = runs[0]
    conclusion = latest["conclusion"] or "in_progress"
    html_url = latest["html_url"]

    return (
        f"🧪 *CI Status for:* `{repo}`\n"
        f"📄 *Workflow:* `{workflow_name}`\n"
        f"🚦 *Status:* *{conclusion}*\n"
        f"🔗 <{html_url}|View on GitHub>"
    )
