"""Simple test to verify OpenAI API key works."""
import os

# Keep proxy settings as they are
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")
print()

try:
    from openai import OpenAI

    # Use the proxy settings that are already in environment
    client = OpenAI(
        api_key="YOUR_OPENAI_API_KEY_HERE"
    )

    print("Attempting to list models...")
    models = client.models.list()
    print(f"SUCCESS! Found {len(models.data)} models")
    print("First few models:", [m.id for m in models.data[:3]])

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

    # Try with max_retries=0 to get clearer error
    print("\nTrying with timeout and max_retries settings...")
    try:
        from openai import OpenAI
        import httpx

        client = OpenAI(
            api_key="YOUR_OPENAI_API_KEY_HERE",
            timeout=60.0,
            max_retries=0,
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print(f"SUCCESS! Response: {response.choices[0].message.content}")

    except Exception as e2:
        print(f"Also failed: {type(e2).__name__}: {e2}")
        import traceback
        traceback.print_exc()
