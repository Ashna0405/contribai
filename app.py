import json
import os
import requests
import threading
import queue
from flask import Flask, render_template, request, Response, stream_with_context, session, redirect, url_for, jsonify
from dotenv import load_dotenv

load_dotenv()

from github.github_client import get_issue
from agents.issue_reader_agent import read_issue
from agents.planner_agent import plan_issue
from agents.code_explorer_agent import explore_codebase
from agents.solution_agent import suggest_solution
from agents.pr_helper_agent import draft_pr
from memory.session_store import session as agent_session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "contribai2026")

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")

# Store user history in memory (simple version)
user_history = {}

def run_pipeline(owner, repo, issue_number, result_queue):
    try:
        agent_session.clear()
        result_queue.put({"agent": "issue_reader", "status": "running"})
        issue_data = get_issue(owner, repo, issue_number)
        if "error" in issue_data:
            result_queue.put({"agent": "issue_reader", "status": "error", "data": issue_data})
            result_queue.put({"done": True})
            return
        parsed = read_issue(issue_data)
        result_queue.put({"agent": "issue_reader", "status": "done", "data": parsed})

        result_queue.put({"agent": "planner", "status": "running"})
        plan = plan_issue(parsed)
        result_queue.put({"agent": "planner", "status": "done", "data": plan})

        result_queue.put({"agent": "code_explorer", "status": "running"})
        exploration = explore_codebase(plan)
        result_queue.put({"agent": "code_explorer", "status": "done", "data": exploration})

        result_queue.put({"agent": "solution", "status": "running"})
        solution = suggest_solution(parsed, plan, exploration)
        result_queue.put({"agent": "solution", "status": "done", "data": solution})

        result_queue.put({"agent": "pr_helper", "status": "running"})
        pr = draft_pr(parsed, plan, exploration, solution)
        result_queue.put({"agent": "pr_helper", "status": "done", "data": pr})

        result_queue.put({"done": True, "all": agent_session.get_all()})

    except Exception as e:
        result_queue.put({"error": str(e)})
        result_queue.put({"done": True})


@app.route("/")
def index():
    user = session.get("user")
    if not user:
        return render_template("login.html")
    return render_template("index.html", user=user)


@app.route("/auth/login")
def login():
    return redirect(
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&scope=repo,user"
    )


@app.route("/auth/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect("/")

    # Exchange code for token
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
        }
    )
    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return redirect("/")

    # Get user info
    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {access_token}"}
    )
    user_data = user_response.json()

    # Save to session
    session["user"] = {
        "login": user_data.get("login"),
        "name": user_data.get("name") or user_data.get("login"),
        "avatar": user_data.get("avatar_url"),
        "token": access_token
    }

    return redirect("/")


@app.route("/auth/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect("/")
    return render_template("dashboard.html", user=user)

@app.route("/history")
def history():
    user = session.get("user")
    if not user:
        return jsonify([])
    return jsonify(user_history.get(user["login"], []))


@app.route("/run")
def run():
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    owner = request.args.get("owner", "psf")
    repo = request.args.get("repo", "requests")
    issue_number = int(request.args.get("issue", 5915))

    result_queue = queue.Queue()
    thread = threading.Thread(
        target=run_pipeline,
        args=(owner, repo, issue_number, result_queue)
    )
    thread.start()

    def generate():
        while True:
            try:
                item = result_queue.get(timeout=60)

                # Save to history when done
                if item.get("done") and item.get("all"):
                    username = user["login"]
                    if username not in user_history:
                        user_history[username] = []
                    user_history[username].insert(0, {
                        "repo": f"{owner}/{repo}",
                        "issue": issue_number,
                        "pr_title": item["all"].get("pr_helper", {}).get("title", ""),
                        "confidence": item["all"].get("pr_helper", {}).get("confidence", 0),
                        "issue_type": item["all"].get("planner", {}).get("issue_type", ""),
                        "agent_scores": {
                            "issue_reader": item["all"].get("issue_reader", {}).get("confidence", 0),
                            "planner": item["all"].get("planner", {}).get("confidence", 0),
                            "code_explorer": item["all"].get("code_explorer", {}).get("confidence", 0),
                            "solution": item["all"].get("solution", {}).get("confidence", 0),
                            "pr_helper": item["all"].get("pr_helper", {}).get("confidence", 0)
                        }
                    })
                    # Keep only last 10
                    user_history[username] = user_history[username][:10]

                yield f"data: {json.dumps(item)}\n\n"
                if item.get("done") or item.get("error"):
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'error': 'Timeout'})}\n\n"
                break

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), threaded=True)
