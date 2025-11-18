"""Test if Anthropic API works through the proxy."""
import os

# Check if there's an Anthropic API key
anthropic_key = os.environ.get('ANTHROPIC_API_KEY', 'NOT_SET')
print(f"ANTHROPIC_API_KEY: {anthropic_key[:20]}..." if anthropic_key != 'NOT_SET' else "ANTHROPIC_API_KEY: NOT_SET")
print(f"ANTHROPIC_BASE_URL: {os.environ.get('ANTHROPIC_BASE_URL')}")
print()

# Try to import and use anthropic
try:
    import anthropic

    client = anthropic.Anthropic(
        api_key=anthropic_key if anthropic_key != 'NOT_SET' else "sk-ant-test"
    )

    print("Attempting to create a message...")
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=10,
        messages=[{"role": "user", "content": "Say 'test'"}]
    )
    print(f"SUCCESS! Response: {message.content[0].text}")

except ImportError:
    print("Anthropic library not installed. Installing...")
    import subprocess
    subprocess.run(["uv", "pip", "install", "anthropic"], check=True)
    print("Please run this script again.")

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
