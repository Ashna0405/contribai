import os
import re
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

def ask_llm(system_prompt: str, user_prompt: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=1024,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            wait = 2 ** attempt
            print(f"[LLM] Attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)
    return "LLM unavailable after retries."

def ask_llm_json(system_prompt: str, user_prompt: str) -> dict:
    raw = ask_llm(system_prompt, user_prompt + "\n\nRespond ONLY with valid JSON. No explanation, no markdown code fences.")
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"[LLM] JSON parse failed. Raw:\n{raw}")
        return {"error": "Could not parse LLM response", "raw": raw}
