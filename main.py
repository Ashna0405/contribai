"""
main.py
Fixed: confidence bars now render correctly. Memory wiring verified.
"""

import json
from dotenv import load_dotenv

load_dotenv()

from github.github_client import get_issue
from agents.issue_reader_agent import read_issue
from agents.planner_agent import plan_issue
from agents.code_explorer_agent import explore_codebase
from agents.solution_agent import suggest_solution
from agents.pr_helper_agent import draft_pr
from memory.session_store import session


def print_separator(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


if __name__ == "__main__":
    owner = "psf"
    repo = "requests"
    issue_number = 5915

    print(f"\n🚀 IssueAI Pipeline Starting")
    print(f"   Repo: {owner}/{repo} | Issue: #{issue_number}")

    # Clear memory for fresh run
    session.clear()

    # ── Agent 1 ───────────────────────────────────────────────
    print_separator("Agent 1 — Issue Reader")
    issue_data = get_issue(owner, repo, issue_number)
    if "error" in issue_data:
        print(f"❌ Could not fetch issue: {issue_data['error']}")
        exit(1)
    parsed_issue = read_issue(issue_data)
    print("\n--- ISSUE ---")
    print(json.dumps(parsed_issue, indent=2))

    # Verify memory saved correctly
    assert session.get("issue_reader"), "❌ IssueReader did not save to session!"
    print("✅ IssueReader saved to session memory.")

    # ── Agent 2 ───────────────────────────────────────────────
    print_separator("Agent 2 — Planner")
    plan = plan_issue(parsed_issue)
    print("\n--- PLAN ---")
    print(json.dumps(plan, indent=2))
    assert session.get("planner"), "❌ Planner did not save to session!"
    print("✅ Planner saved to session memory.")

    # ── Agent 3 ───────────────────────────────────────────────
    print_separator("Agent 3 — Code Explorer")
    exploration = explore_codebase(plan)
    print("\n--- CODE EXPLORATION ---")
    print(json.dumps(exploration, indent=2))
    assert session.get("code_explorer"), "❌ CodeExplorer did not save to session!"
    print("✅ CodeExplorer saved to session memory.")

    # ── Agent 4 ───────────────────────────────────────────────
    print_separator("Agent 4 — Solution")
    solution = suggest_solution(parsed_issue, plan, exploration)
    print("\n--- SOLUTION STRATEGY ---")
    print(json.dumps(solution, indent=2))
    assert session.get("solution"), "❌ Solution did not save to session!"
    print("✅ Solution saved to session memory.")

    # ── Agent 5 ───────────────────────────────────────────────
    print_separator("Agent 5 — PR Helper")
    pr = draft_pr(parsed_issue, plan, exploration, solution)
    print("\n--- PULL REQUEST DRAFT ---")
    print(json.dumps(pr, indent=2))
    assert session.get("pr_helper"), "❌ PRHelper did not save to session!"
    print("✅ PRHelper saved to session memory.")

    # ── Summary ───────────────────────────────────────────────
    print_separator("Pipeline Complete ✅")
    print(f"📁 Full output saved to: data/output.json\n")

    print("📊 Confidence Scores:")
    for agent_key in ["issue_reader", "planner", "code_explorer", "solution", "pr_helper"]:
        data = session.get(agent_key)
        score = data.get("confidence", None)
        if isinstance(score, (float, int)):
            filled = int(score * 10)
            bar = "\u2588" * filled + "\u2591" * (10 - filled)
            print(f"   {agent_key:<20} [{bar}] {score:.1f}")
        else:
            print(f"   {agent_key:<20} [N/A]")

    print(f"\n🎯 PR Title  : {session.get('pr_helper').get('title', 'N/A')}")
    print(f"🔍 Files     : {', '.join(session.get('code_explorer').get('files_to_check', []))}")
    print(f"\n✅ All agents sharing memory correctly!")
