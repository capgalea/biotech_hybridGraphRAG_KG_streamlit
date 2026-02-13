import os
import openai
from dotenv import load_dotenv

# Find .env in project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path)

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    print("ERROR: DEEPSEEK_API_KEY not found in .env")
    exit(1)

print(f"DEEPSEEK_API_KEY found: {api_key[:8]}...{api_key[-5:]}")

try:
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    
    response = client.chat.completions.create(
        model="deepseek/deepseek-v3.2",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello, are you working?"},
        ],
        max_tokens=20,
        stream=False
    )
    
    print("SUCCESS: DeepSeek API is working!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"ERROR: DeepSeek API call failed: {str(e)}")
