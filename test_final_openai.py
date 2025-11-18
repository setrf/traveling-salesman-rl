"""Final test to see if the provided OpenAI key is actually valid."""
import os

# Restore proxy settings for one more test with the proxy allowing the request
os.environ['HTTP_PROXY'] = 'http://container_container_01JiuPXkGnt1nu7SoYc3McMi--claude_code_remote--old-safe-svelte-bushel:noauth@21.0.0.163:15002'
os.environ['HTTPS_PROXY'] = 'http://container_container_01JiuPXkGnt1nu7SoYc3McMi--claude_code_remote--old-safe-svelte-bushel:noauth@21.0.0.163:15002'

from openai import OpenAI

# Maybe the issue is the key is expired/invalid and we're getting a generic error?
# Let's test with a known invalid key to compare errors
print("Test 1: Testing with provided key...")
try:
    client = OpenAI(api_key="YOUR_OPENAI_API_KEY_HERE")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print(f"Success: {response.choices[0].message.content}")
except Exception as e:
    print(f"Error with provided key: {type(e).__name__}: {e}")

print("\nTest 2: Testing with obviously invalid key...")
try:
    client = OpenAI(api_key="sk-invalid")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print(f"Success: {response.choices[0].message.content}")
except Exception as e:
    print(f"Error with invalid key: {type(e).__name__}: {e}")
