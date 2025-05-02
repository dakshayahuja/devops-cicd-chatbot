import os
import requests
from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse
from github.client import get_latest_workflow_status

app = FastAPI()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")  # or use channel ID


@app.post("/slack/events")
async def slack_events(request: Request):
    form = await request.form()
    text = form.get("text")
    user_id = form.get("user_id")
    channel_id = form.get("channel_id") or SLACK_CHANNEL

    parts = text.strip().split()
    if len(parts) < 2:
        message = "⚠️ Usage: `/cicd-status github <repo> [workflow]`"
    elif "github" in parts[0].lower():
        repo = parts[1]
        workflow_name = parts[2] if len(parts) >= 3 else None
        message = get_latest_workflow_status(repo, workflow_name)
    else:
        message = "🛠 Please specify a valid system like `github`."

    # Send as persistent message using chat.postMessage
    requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "channel": channel_id,
            "text": f"<@{user_id}> requested CI/CD status:\n{message}"
        }
    )

    # Respond quickly to slash command (ack)
    return Response(status_code=204)

@app.post("/github/webhook")
async def github_webhook(request: Request):
    body = await request.json()

    # GitHub sends multiple event types, filter
    if body.get("action") == "completed" and "workflow_run" in body:
        run = body["workflow_run"]
        if run.get("conclusion") == "failure":
            repo = run["repository"]["full_name"]
            name = run["name"]
            url = run["html_url"]

            message = (
                f"❌ *CI FAILED!*\n"
                f"📦 *Repo:* `{repo}`\n"
                f"📄 *Workflow:* `{name}`\n"
                f"🔗 <{url}|View Run>"
            )

            print(message)
            # Send to Slack
            requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "channel": SLACK_CHANNEL,
                    "text": message
                }
            )

    return JSONResponse(content={"status": "ok"})