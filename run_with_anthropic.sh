#!/bin/bash
# Wrapper script to run vf-eval using Anthropic API via local proxy

set -e

# Check for Anthropic API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable is not set"
    echo ""
    echo "The OpenAI API is blocked by the proxy, but Anthropic API is accessible."
    echo "Please set your Anthropic API key:"
    echo ""
    echo "  export ANTHROPIC_API_KEY='your-anthropic-api-key-here'"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "Anthropic API key found: ${ANTHROPIC_API_KEY:0:20}..."
echo ""

# Test Anthropic API access
echo "Testing Anthropic API access..."
python3 << 'EOF'
import os
import anthropic

try:
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=10,
        messages=[{"role": "user", "content": "Say 'test'"}]
    )
    print(f"✓ Anthropic API working! Response: {response.content[0].text}")
except Exception as e:
    print(f"✗ Anthropic API test failed: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "Anthropic API test failed. Please check your API key."
    exit 1
fi

echo ""
echo "Starting OpenAI-to-Anthropic proxy server..."
echo ""

# Start the proxy server in the background
python3 openai_to_anthropic_proxy.py 8765 &
PROXY_PID=$!

# Ensure proxy is killed on exit
trap "echo 'Stopping proxy...'; kill $PROXY_PID 2>/dev/null || true" EXIT

# Wait for proxy to start
sleep 2

# Test the proxy
echo "Testing proxy server..."
curl -s http://127.0.0.1:8765/health | grep -q "ok" && echo "✓ Proxy server is running" || (echo "✗ Proxy server failed to start"; exit 1)

echo ""
echo "Running vf-eval with proxy..."
echo ""

# Set OpenAI API key to dummy value (proxy doesn't use it)
export OPENAI_API_KEY="sk-dummy-key-for-proxy"

# Run vf-eval with the proxy
uv run vf-eval tsp_rl_env \
    --api-base-url http://127.0.0.1:8765/v1 \
    -n 2 \
    -r 1 \
    -m gpt-4o-mini \
    "$@"

echo ""
echo "Evaluation complete!"
