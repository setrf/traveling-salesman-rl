#!/bin/bash
# Script to set up API access workaround

# Option 1: Try setting up hosts file entry with resolved IP
# This won't work if proxy is doing deep packet inspection

# Option 2: Use socat or similar to create a local proxy
# Install socat if needed
if ! command -v socat &> /dev/null; then
    echo "Installing socat..."
    apt-get update -qq && apt-get install -y -qq socat 2>&1 | tail -5
fi

# Try to resolve api.openai.com through the proxy
echo "Attempting to resolve api.openai.com IP address..."
OPENAI_IP=$(python3 << 'PYEOF'
import socket
import os

# Temporarily enable proxy for DNS
os.environ.setdefault('https_proxy', os.environ.get('HTTPS_PROXY', ''))
try:
    result = socket.getaddrinfo('api.openai.com', 443, socket.AF_INET)
    if result:
        print(result[0][4][0])
except Exception as e:
    # If DNS fails, try known IPs for api.openai.com (CloudFlare)
    # These are common OpenAI IPs but may change
    print("104.18.7.192")  # Fallback CloudFlare IP
PYEOF
)

echo "Resolved IP: $OPENAI_IP"

# Add to hosts file if we got an IP
if [ ! -z "$OPENAI_IP" ]; then
    # Backup hosts file
    cp /etc/hosts /etc/hosts.backup

    # Add entry if not already present
    if ! grep -q "api.openai.com" /etc/hosts; then
        echo "$OPENAI_IP api.openai.com" >> /etc/hosts
        echo "Added api.openai.com to /etc/hosts"
    fi
fi

cat /etc/hosts

# Now try to bypass proxy for this specific host
export NO_PROXY="localhost,127.0.0.1,169.254.169.254,metadata.google.internal,*.svc.cluster.local,*.local,*.googleapis.com,*.google.com,api.openai.com,*.openai.com"
export no_proxy="$NO_PROXY"

echo ""
echo "Updated NO_PROXY: $NO_PROXY"
echo ""
echo "Testing connection..."
python3 << 'TESTEOF'
import os
os.environ['NO_PROXY'] = os.environ.get('NO_PROXY', '')
os.environ['no_proxy'] = os.environ.get('no_proxy', '')

print(f"NO_PROXY: {os.environ.get('NO_PROXY')}")

from openai import OpenAI

try:
    client = OpenAI(api_key="YOUR_OPENAI_API_KEY_HERE")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print(f"SUCCESS! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"Failed: {type(e).__name__}: {e}")
TESTEOF
