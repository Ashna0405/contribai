"""
app.py
Flask backend — connects your existing agents to the web UI.
Run with: python app.py
"""

import json
import os
import queue
import threading
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from dotenv import load_dotenv

load_dotenv()

from github.github_client import get_issue
from agents.issue_reader_agent import read_issue
from agents.planner_agent import plan_issue
from agents.code_explorer_agent import explore_codebase
from agents.solution_agent import suggest_solution
from agents.pr_helper_agent import draft_pr
from memory.session_store import session

app = Flask(__name__)


def run_pipeline(owner, repo, issue_number, result_queue):
    """Runs the full agent pipeline and pushes results into the queue."""
    try:
        session.clear()

        # Agent 1
        result_queue.put({"agent": "issue_reader", "status": "running"})
        issue_data = get_issue(owner, repo, issue_number)
        if "error" in issue_data:
            result_queue.put({"agent": "issue_reader", "status": "error", "data": issue_data})
            result_queue.put({"done": True})
            return
        parsed = read_issue(issue_data)
        result_queue.put({"agent": "issue_reader", "status": "done", "data": parsed})

        # Agent 2
        result_queue.put({"agent": "planner", "status": "running"})
        plan = plan_issue(parsed)
        result_queue.put({"agent": "planner", "status": "done", "data": plan})

        # Agent 3
        result_queue.put({"agent": "code_explorer", "status": "running"})
        exploration = explore_codebase(plan)
        result_queue.put({"agent": "code_explorer", "status": "done", "data": exploration})

        # Agent 4
        result_queue.put({"agent": "solution", "status": "running"})
        solution = suggest_solution(parsed, plan, exploration)
        result_queue.put({"agent": "solution", "status": "done", "data": solution})

        # Agent 5
        result_queue.put({"agent": "pr_helper", "status": "running"})
        pr = draft_pr(parsed, plan, exploration, solution)
        result_queue.put({"agent": "pr_helper", "status": "done", "data": pr})

        result_queue.put({"done": True})

    except Exception as e:
        result_queue.put({"error": str(e)})
        result_queue.put({"done": True})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run", methods=["GET"])
def run():
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
                yield f"data: {json.dumps(item)}\n\n"
                if item.get("done") or item.get("error"):
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'error': 'Timeout'})}\n\n"
                break

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), threaded=True)