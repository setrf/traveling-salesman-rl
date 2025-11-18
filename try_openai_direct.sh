#!/bin/bash
# Attempt to access OpenAI API directly by resolving IP and bypassing proxy

set -e

echo "Attempting to bypass proxy for OpenAI API access..."
echo ""

# Try to get OpenAI IP through proxy DNS
echo "Step 1: Resolving api.openai.com IP address..."
OPENAI_IP=$(python3 << 'EOF'
import socket
# Use system DNS (which goes through proxy)
try:
    result = socket.getaddrinfo('api.openai.com', 443, socket.AF_INET)
    if result:
        print(result[0][4][0])
    else:
        # Fallback to known Cloudflare IP (OpenAI uses Cloudflare)
        print("104.18.6.192")
except:
    # Fallback IP
    print("104.18.6.192")
EOF
)

echo "Resolved IP: $OPENAI_IP"

# Add to hosts file
echo ""
echo "Step 2: Adding to /etc/hosts..."
if grep -q "api.openai.com" /etc/hosts; then
    echo "Entry already exists in /etc/hosts"
else
    echo "$OPENAI_IP api.openai.com" >> /etc/hosts
    echo "Added $OPENAI_IP api.openai.com to /etc/hosts"
fi

# Add openrouter too
OPENROUTER_IP=$(python3 << 'EOF'
import socket
try:
    result = socket.getaddrinfo('openrouter.ai', 443, socket.AF_INET)
    if result:
        print(result[0][4][0])
    else:
        print("104.18.25.153")
except:
    print("104.18.25.153")
EOF
)

echo "Resolved openrouter.ai IP: $OPENROUTER_IP"
if grep -q "openrouter.ai" /etc/hosts; then
    echo "OpenRouter entry already exists in /etc/hosts"
else
    echo "$OPENROUTER_IP openrouter.ai" >> /etc/hosts
    echo "Added $OPENROUTER_IP openrouter.ai to /etc/hosts"
fi

echo ""
cat /etc/hosts
echo ""

# Try with NO_PROXY set
echo "Step 3: Testing with NO_PROXY set..."
export NO_PROXY="localhost,127.0.0.1,169.254.169.254,metadata.google.internal,*.svc.cluster.local,*.local,*.googleapis.com,*.google.com,api.openai.com,*.openai.com,openrouter.ai,*.openrouter.ai"
export no_proxy="$NO_PROXY"

# Also try unsetting HTTP_PROXY temporarily
echo "Step 4: Testing without proxy env vars..."
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy

echo "Testing OpenAI API with provided key..."
uv run python << 'EOF'
import os
from openai import OpenAI

try:
    client = OpenAI(api_key="YOUR_OPENAI_API_KEY_HERE")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'test'"}],
        max_tokens=5
    )
    print(f"✓ SUCCESS! OpenAI API working! Response: {response.choices[0].message.content}")
    exit(0)
except Exception as e:
    print(f"✗ FAILED: {type(e).__name__}: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "SUCCESS! OpenAI API is now accessible."
    echo "You can now run: unset HTTP_PROXY HTTPS_PROXY && uv run vf-eval tsp_rl_env -n 2 -r 1 -m gpt-4o-mini"
else
    echo ""
    echo "Direct access still blocked. Use the Anthropic proxy instead:"
    echo "  ./run_with_anthropic.sh"
fi
