#!/usr/bin/env python3
"""
Test the OpenAI-to-Anthropic proxy with a mock Anthropic backend.
This demonstrates that the proxy works correctly even without a real API key.
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import requests


class MockAnthropicHandler(BaseHTTPRequestHandler):
    """Mock Anthropic API server for testing."""

    def do_POST(self):
        if self.path == "/v1/messages":
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length))

            # Return a mock response
            response = {
                "id": "msg_test123",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Test response from mock Anthropic API"
                    }
                ],
                "model": body.get("model", "claude-3-5-haiku-20241022"),
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 5,
                },
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Suppress logs


def run_mock_anthropic(port=9999):
    """Run mock Anthropic API server."""
    server = HTTPServer(("127.0.0.1", port), MockAnthropicHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_proxy():
    """Test the OpenAI-to-Anthropic proxy."""
    import os
    import sys

    # Start mock Anthropic server
    print("Starting mock Anthropic API server on port 9999...")
    mock_server = run_mock_anthropic(9999)
    time.sleep(0.5)

    # Override Anthropic base URL to point to our mock
    os.environ["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:9999"
    os.environ["ANTHROPIC_API_KEY"] = "mock-key-for-testing"

    # Start the proxy server in a thread
    print("Starting OpenAI-to-Anthropic proxy on port 8765...")
    from openai_to_anthropic_proxy import OpenAIToAnthropicHandler

    def run_proxy():
        proxy_server = HTTPServer(("127.0.0.1", 8765), OpenAIToAnthropicHandler)
        proxy_server.serve_forever()

    proxy_thread = Thread(target=run_proxy, daemon=True)
    proxy_thread.start()
    time.sleep(1)

    # Test the proxy with OpenAI client
    print("\nTesting proxy with OpenAI-format request...")
    try:
        response = requests.post(
            "http://127.0.0.1:8765/v1/chat/completions",
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello from proxy!'"},
                ],
                "max_tokens": 50,
            },
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS! Proxy is working correctly")
            print(f"  Request model: gpt-4o-mini")
            print(f"  Response: {json.dumps(data, indent=2)}")
            print(f"\n  Message content: {data['choices'][0]['message']['content']}")
            return True
        else:
            print(f"✗ FAILED! Status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ FAILED! Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 80)
    print("OpenAI-to-Anthropic Proxy Test")
    print("=" * 80)
    print()

    success = test_proxy()

    print()
    print("=" * 80)
    if success:
        print("✓ Proxy test PASSED!")
        print()
        print("The proxy correctly:")
        print("  1. Accepts OpenAI-format requests")
        print("  2. Translates to Anthropic-format")
        print("  3. Returns OpenAI-format responses")
        print()
        print("You can now use it with vf-eval by:")
        print("  1. Setting ANTHROPIC_API_KEY environment variable")
        print("  2. Running: ./run_with_anthropic.sh")
    else:
        print("✗ Proxy test FAILED")
        print("Check the error messages above")

    print("=" * 80)
