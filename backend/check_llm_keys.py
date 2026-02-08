from app.config import settings

print("=== LLM API Keys Status ===")
print(f"OpenAI:    {'SET ✓' if settings['openai']['api_key'] else 'NOT SET ✗'}")
print(f"Anthropic: {'SET ✓' if settings['anthropic']['api_key'] else 'NOT SET ✗'}")
print(f"Google:    {'SET ✓' if settings['google']['api_key'] else 'NOT SET ✗'}")
print(f"DeepSeek:  {'SET ✓' if settings['deepseek']['api_key'] else 'NOT SET ✗'}")

# Show which keys are available
available = []
if settings['openai']['api_key']:
    available.append('OpenAI')
if settings['anthropic']['api_key']:
    available.append('Anthropic')
if settings['google']['api_key']:
    available.append('Google')
if settings['deepseek']['api_key']:
    available.append('DeepSeek')

print(f"\nAvailable LLMs: {', '.join(available) if available else 'NONE'}")

if not available:
    print("\n⚠️  WARNING: No LLM API keys configured!")
    print("The Query & Chat feature requires at least one LLM API key.")
    print("\nTo fix this, add one of the following to your .env file:")
    print("  - ANTHROPIC_API_KEY=sk-ant-...")
    print("  - OPENAI_API_KEY=sk-...")
    print("  - GOOGLE_API_KEY=...")
    print("  - DEEPSEEK_API_KEY=...")
