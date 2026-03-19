"""
agents/solution_agent.py
Upgraded from your original suggest_solution() function.
Before: hardcoded streaming-related strings regardless of the actual issue.
Now: LLM reads full pipeline context and suggests a real, issue-specific solution.
"""

from llm.llm_client import ask_llm_json
from memory.session_store import session

SYSTEM_PROMPT = """
You are a senior open source contributor and software architect.
Your job is to propose a clear, practical, issue-specific solution based on 
full analysis from a team of specialized agents.
Think like a developer who will actually implement this. Always respond with valid JSON only.
"""


def suggest_solution(issue: dict = None, plan: dict = None, exploration: dict = None) -> dict:
    """
    Upgraded from your original version.
    Before: took issue/plan/exploration as args, returned hardcoded streaming fixes.
    Now: reads full session memory, uses LLM for real issue-specific solution.
    Args kept for backward compatibility with your main.py call signature.
    """
    if not session.get("issue_reader"):
        print("[Solution] Missing data in session. Run previous agents first.")
        return {"error": "Run all previous agents first.",
                "proposed_fix": [], "logic_changes": [], "tests_to_add": [], "risks": []}

    user_prompt = f"""
Using the full analysis from the pipeline, propose a concrete solution to this GitHub issue.

Full pipeline context:
{session.summary()}

Return a JSON object with these exact keys:
- "proposed_fix": list of 3-5 specific code-level changes to implement (list of strings)
- "implementation_steps": ordered step-by-step implementation instructions (list of strings)
- "logic_changes": list of specific logic or algorithm changes needed (list of strings)
- "files_to_modify": list of files that need to be changed (list of strings)
- "code_hints": short pseudocode or hints showing HOW to implement each fix (list of strings)
- "tests_to_add": list of specific test cases to write (list of strings)
- "risks": list of potential risks or side effects of this fix (list of strings)
- "alternative_approaches": list of 1-2 alternative ways to solve this (list of strings)
- "confidence": your confidence from 0.0 to 1.0 in this solution (float)
"""

    print("[Solution] Generating solution with LLM...")
    result = ask_llm_json(SYSTEM_PROMPT, user_prompt)

    session.set("solution", result)
    print(f"[Solution] Done. Confidence: {result.get('confidence')} | Risks: {len(result.get('risks', []))}")
    return result