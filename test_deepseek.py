"""Connectivity test for the DeepSeek API key in grantscribe/.env.

Prints the model's reply and token usage. NEVER prints the key.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(ENV_PATH)

api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
if not api_key:
    raise SystemExit(f"DEEPSEEK_API_KEY is empty/missing in {ENV_PATH} — paste the key and retry.")

base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
model = os.environ.get("DEEPSEEK_MODEL_FAST", "deepseek-v4-flash")

client = OpenAI(api_key=api_key, base_url=base_url)
resp = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Reply with exactly: GrantScribe key OK"}],
    max_tokens=20,
    temperature=0,
)

print(f"base_url : {base_url}")
print(f"model    : {model}")
print(f"reply    : {resp.choices[0].message.content!r}")
print(f"usage    : {resp.usage}")
print("\nOK: DeepSeek key works.")
