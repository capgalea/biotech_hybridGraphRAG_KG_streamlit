import os
import anthropic
from dotenv import load_dotenv

# Resolve project root and load .env from there
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=DOTENV_PATH)

api_key = os.getenv("ANTHROPIC_API_KEY")

print(f"ANTHROPIC_API_KEY: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")

if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not found in .env")
    exit(1)

try:
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hello, are you working?"}]
    )
    print("SUCCESS: Anthropic API is working!")
    print(f"Response: {message.content[0].text}")
except Exception as e:
    print(f"ERROR: Anthropic API call failed: {str(e)}")
