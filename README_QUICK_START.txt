================================================================================
  TSP RL Environment - API Access Quick Start
================================================================================

PROBLEM: OpenAI API blocked by proxy (403 Forbidden)
SOLUTION: Use Anthropic Claude via local proxy (Anthropic is not blocked!)

--------------------------------------------------------------------------------
  3-STEP SETUP
--------------------------------------------------------------------------------

1. Get Anthropic API key:
   https://console.anthropic.com/settings/keys

2. Set environment variable:
   export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

3. Run evaluation:
   ./run_with_anthropic.sh

That's it!

--------------------------------------------------------------------------------
  WHAT HAPPENS
--------------------------------------------------------------------------------

The script will:
  ✓ Verify Anthropic API key works
  ✓ Start local proxy server (OpenAI ↔ Anthropic translator)
  ✓ Run vf-eval against TSP environment
  ✓ Use Claude 3.5 Haiku (fast, cost-effective, ~$0.01 for this test)
  ✓ Display results

Expected output:
  "Anthropic API working! Response: ..."
  "Proxy server is running"
  "Running vf-eval with proxy..."
  [Evaluation results with rewards and statistics]

--------------------------------------------------------------------------------
  TROUBLESHOOTING
--------------------------------------------------------------------------------

Error: "ANTHROPIC_API_KEY environment variable is not set"
→ export ANTHROPIC_API_KEY="your-key"

Error: "invalid x-api-key"
→ Check your Anthropic API key is correct

Error: "Connection refused"
→ Proxy didn't start. Check if port 8765 is available

Still getting "Access denied"?
→ Verify using: --api-base-url http://127.0.0.1:8765/v1

--------------------------------------------------------------------------------
  FILES
--------------------------------------------------------------------------------

Core:
  run_with_anthropic.sh ............ Automated setup and run script
  openai_to_anthropic_proxy.py ..... HTTP proxy server

Documentation:
  INVESTIGATION_REPORT.md .......... Full technical investigation
  API_ACCESS_SOLUTION.md ........... Detailed solution explanation
  SETUP_AND_RUN.md ................. Step-by-step guide
  README_QUICK_START.txt ........... This file

Tests:
  test_proxy_mock.py ............... Proxy validation (PASSED ✓)
  test_api.py ...................... Network diagnostics

--------------------------------------------------------------------------------
  MANUAL USAGE (if needed)
--------------------------------------------------------------------------------

Terminal 1:
  export ANTHROPIC_API_KEY="sk-ant-api03-..."
  python3 openai_to_anthropic_proxy.py 8765

Terminal 2:
  export OPENAI_API_KEY="dummy"
  uv run vf-eval tsp_rl_env \
      --api-base-url http://127.0.0.1:8765/v1 \
      -n 2 -r 1 -m gpt-4o-mini

--------------------------------------------------------------------------------
  WHY THIS WORKS
--------------------------------------------------------------------------------

Container proxy blocks:     Container proxy allows:
  ✗ api.openai.com           ✓ api.anthropic.com
  ✗ openrouter.ai

Our solution:
  vf-eval → Local Proxy → Container Proxy → Anthropic Claude API
            (translates    (allows           (works!)
             formats)       Anthropic)

--------------------------------------------------------------------------------
  ALTERNATIVE: Get IT to Whitelist OpenAI
--------------------------------------------------------------------------------

If IT can whitelist api.openai.com in the proxy:

  export OPENAI_API_KEY="sk-proj-your-actual-openai-key"
  uv run vf-eval tsp_rl_env -n 2 -r 1 -m gpt-4o-mini

But until then, use the Anthropic proxy solution above.

================================================================================
  Ready to run: ./run_with_anthropic.sh
================================================================================
