#!/usr/bin/env python3
"""
OpenAI-to-Anthropic API Proxy Server

This creates a local server that accepts OpenAI API requests and translates them
to Anthropic API calls, allowing vf-eval to work despite the OpenAI proxy block.
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


class OpenAIToAnthropicHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests to OpenAI-compatible endpoints."""
        path = urlparse(self.path).path

        if path == "/v1/chat/completions":
            self.handle_chat_completions()
        else:
            self.send_error(404, f"Path not found: {path}")

    def do_GET(self):
        """Handle GET requests."""
        path = urlparse(self.path).path

        if path == "/v1/models":
            self.handle_models_list()
        elif path == "/health":
            self.send_json_response({"status": "ok"}, 200)
        else:
            self.send_error(404, f"Path not found: {path}")

    def handle_models_list(self):
        """Return a list of available models."""
        models = {
            "object": "list",
            "data": [
                {
                    "id": "gpt-4o-mini",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "anthropic-proxy",
                },
                {
                    "id": "gpt-4o",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "anthropic-proxy",
                },
            ],
        }
        self.send_json_response(models, 200)

    def handle_chat_completions(self):
        """Handle chat completions by proxying to Anthropic."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            openai_request = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        # Translate OpenAI request to Anthropic format
        messages = openai_request.get("messages", [])
        model = openai_request.get("model", "gpt-4o-mini")
        max_tokens = openai_request.get("max_tokens", 1024)
        temperature = openai_request.get("temperature", 1.0)

        # Map OpenAI model names to Claude models
        model_map = {
            "gpt-4o-mini": "claude-3-5-haiku-20241022",
            "gpt-4o": "claude-3-5-sonnet-20241022",
            "gpt-4": "claude-3-5-sonnet-20241022",
        }
        claude_model = model_map.get(model, "claude-3-5-haiku-20241022")

        # Convert OpenAI messages to Anthropic format
        anthropic_messages = []
        system_prompt = None

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                system_prompt = content
            elif role in ["user", "assistant"]:
                anthropic_messages.append({"role": role, "content": content})

        # Call Anthropic API
        try:
            import anthropic

            # Get API key from environment (set by wrapper script)
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                self.send_error(500, "ANTHROPIC_API_KEY not set")
                return

            client = anthropic.Anthropic(api_key=api_key)

            # Create message with Anthropic
            anthropic_kwargs = {
                "model": claude_model,
                "max_tokens": max_tokens,
                "messages": anthropic_messages,
            }

            if system_prompt:
                anthropic_kwargs["system"] = system_prompt

            if temperature is not None:
                anthropic_kwargs["temperature"] = temperature

            response = client.messages.create(**anthropic_kwargs)

            # Convert Anthropic response to OpenAI format
            openai_response = {
                "id": response.id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response.content[0].text,
                        },
                        "finish_reason": response.stop_reason,
                    }
                ],
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                },
            }

            self.send_json_response(openai_response, 200)

        except Exception as e:
            print(f"Error calling Anthropic API: {e}")
            import traceback

            traceback.print_exc()
            self.send_error(500, f"Anthropic API error: {str(e)}")

    def send_json_response(self, data, status_code=200):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=8765):
    """Run the proxy server."""
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, OpenAIToAnthropicHandler)
    print(f"Starting OpenAI-to-Anthropic proxy on http://127.0.0.1:{port}")
    print(f"Configure vf-eval with: --api-base-url http://127.0.0.1:{port}/v1")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    run_server(port)
