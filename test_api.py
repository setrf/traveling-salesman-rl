"""Test OpenAI API access with different proxy configurations."""
import os
import sys

def test_api_with_proxy():
    """Test API call with current proxy settings."""
    print("=" * 80)
    print("TEST 1: API call with current proxy settings")
    print("=" * 80)
    print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'Not set')}")
    print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'Not set')}")
    print(f"NO_PROXY: {os.environ.get('NO_PROXY', 'Not set')}")
    print()

    try:
        from openai import OpenAI
        client = OpenAI(api_key="YOUR_OPENAI_API_KEY_HERE")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API working!'"}],
            max_tokens=10
        )
        print("SUCCESS! Response:", response.choices[0].message.content)
        return True
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return False

def test_api_without_proxy():
    """Test API call with proxy bypassed."""
    print("\n" + "=" * 80)
    print("TEST 2: API call with proxy bypassed (NO_PROXY set)")
    print("=" * 80)

    # Add OpenAI domains to NO_PROXY
    current_no_proxy = os.environ.get('NO_PROXY', '')
    new_no_proxy = current_no_proxy + ',api.openai.com,*.openai.com,openrouter.ai,*.openrouter.ai' if current_no_proxy else 'api.openai.com,*.openai.com,openrouter.ai,*.openrouter.ai'
    os.environ['NO_PROXY'] = new_no_proxy
    os.environ['no_proxy'] = new_no_proxy

    print(f"Updated NO_PROXY: {os.environ['NO_PROXY']}")
    print()

    try:
        from openai import OpenAI
        # Force reload to pick up new proxy settings
        import importlib
        import httpx
        importlib.reload(httpx)

        client = OpenAI(api_key="YOUR_OPENAI_API_KEY_HERE")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API working!'"}],
            max_tokens=10
        )
        print("SUCCESS! Response:", response.choices[0].message.content)
        return True
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return False

def test_api_with_explicit_client():
    """Test API call with httpx client bypassing proxy."""
    print("\n" + "=" * 80)
    print("TEST 3: API call with httpx client bypassing proxy")
    print("=" * 80)

    try:
        from openai import OpenAI
        import httpx

        # Create httpx client that bypasses proxy using mounts
        http_client = httpx.Client(
            mounts={
                "https://": httpx.HTTPTransport(proxy=None),
                "http://": httpx.HTTPTransport(proxy=None),
            },
            timeout=30.0
        )

        client = OpenAI(
            api_key="YOUR_OPENAI_API_KEY_HERE",
            http_client=http_client
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API working!'"}],
            max_tokens=10
        )
        print("SUCCESS! Response:", response.choices[0].message.content)
        return True
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_unset_proxy():
    """Test API call with proxy environment variables temporarily unset."""
    print("\n" + "=" * 80)
    print("TEST 4: API call with proxy env vars temporarily unset")
    print("=" * 80)

    # Save current proxy settings
    saved_proxies = {}
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']

    for var in proxy_vars:
        if var in os.environ:
            saved_proxies[var] = os.environ[var]
            del os.environ[var]

    print("Temporarily unset all proxy environment variables")
    print()

    try:
        from openai import OpenAI

        client = OpenAI(api_key="YOUR_OPENAI_API_KEY_HERE")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API working!'"}],
            max_tokens=10
        )
        print("SUCCESS! Response:", response.choices[0].message.content)
        return True
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore proxy settings
        for var, value in saved_proxies.items():
            os.environ[var] = value

if __name__ == "__main__":
    # Test 1: With proxy (expected to fail)
    test1 = test_api_with_proxy()

    # Test 2: With NO_PROXY updated (might work)
    test2 = test_api_without_proxy()

    # Test 3: With explicit httpx client (most likely to work)
    test3 = test_api_with_explicit_client()

    # Test 4: Unset proxy env vars
    test4 = test_api_unset_proxy()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Test 1 (with proxy): {'PASSED' if test1 else 'FAILED'}")
    print(f"Test 2 (NO_PROXY updated): {'PASSED' if test2 else 'FAILED'}")
    print(f"Test 3 (httpx bypass): {'PASSED' if test3 else 'FAILED'}")
    print(f"Test 4 (unset proxy): {'PASSED' if test4 else 'FAILED'}")

    if test4:
        print("\nRECOMMENDATION: Unset HTTP_PROXY/HTTPS_PROXY environment variables before running")
        sys.exit(0)
    elif test3:
        print("\nRECOMMENDATION: Use httpx client with proxy=None in HTTPTransport")
        sys.exit(0)
    elif test2:
        print("\nRECOMMENDATION: Update NO_PROXY environment variable")
        sys.exit(0)
    elif test1:
        print("\nSUCCESS: Proxy is working fine")
        sys.exit(0)
    else:
        print("\nERROR: All tests failed")
        sys.exit(1)
