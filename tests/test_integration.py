"""
Integration test for TSP RL Environment

Tests the complete pipeline including:
- Environment loading
- Instance generation
- Prompt formatting
- Response parsing
- Reward computation
"""

import sys
from pathlib import Path

# Add environment to path
sys.path.insert(0, str(Path(__file__).parent.parent / "environments" / "tsp_rl_env"))

import asyncio
import verifiers as vf
from tsp_rl_env import (
    generate_synthetic_dataset,
    generate_tsp_instance,
    nearest_neighbor_tour,
    compute_tour_length,
    tsp_reward,
)


async def test_full_pipeline():
    """Test complete environment pipeline with simulated model responses"""
    print("=" * 70)
    print("TSP RL ENVIRONMENT - FULL INTEGRATION TEST")
    print("=" * 70)

    # 1. Load environment
    print("\n[1/6] Loading environment...")
    env = vf.load_environment('tsp_rl_env', num_examples=3, eval_num_examples=2)
    print(f"✓ Environment loaded: {len(env.dataset)} train, {len(env.eval_dataset)} eval")

    # 2. Get a sample instance
    print("\n[2/6] Getting sample instance...")
    sample = env.dataset[0]
    n_cities = sample['n_cities']
    print(f"✓ Instance {sample['instance_id']}: {n_cities} cities")
    print(f"  Baseline length: {sample['baseline_length']:.4f}")

    # 3. Check prompt format
    print("\n[3/6] Checking prompt format...")
    prompt = sample['prompt']
    print(f"✓ Prompt has {len(prompt)} messages")
    print(f"  System prompt: {prompt[0]['content'][:80]}...")
    print(f"  User prompt (first 100 chars): {prompt[1]['content'][:100]}...")

    # 4. Simulate model responses
    print("\n[4/6] Testing reward computation with simulated responses...")

    # Test case 1: Valid tour (baseline tour)
    baseline_tour = sample['baseline_tour']
    valid_response = f'{{"tour": {baseline_tour}}}'

    state = {
        "info": {
            "n_cities": sample['n_cities'],
            "coordinates": sample['coordinates'],
            "distance_matrix": sample['distance_matrix'],
            "baseline_length": sample['baseline_length'],
        }
    }

    reward1 = await tsp_reward(valid_response, "", state)
    print(f"  Case 1 (baseline tour): reward = {reward1:.4f}")
    assert reward1 == 0.0, "Baseline tour should get 0.0 reward (not better than itself)"

    # Test case 2: Better tour (if possible, just reverse for testing)
    # For this test, we'll create a simple valid tour
    simple_tour = list(range(n_cities))
    simple_response = f'{{"tour": {simple_tour}}}'

    state2 = state.copy()
    reward2 = await tsp_reward(simple_response, "", state2)
    print(f"  Case 2 (simple tour 0,1,2,...): reward = {reward2:.4f}")
    assert 0.0 <= reward2 <= 1.0, "Reward should be in [0, 1]"

    # Test case 3: Invalid JSON
    invalid_response = "This is not JSON"
    state3 = state.copy()
    reward3 = await tsp_reward(invalid_response, "", state3)
    print(f"  Case 3 (invalid JSON): reward = {reward3:.4f}")
    assert reward3 == 0.0, "Invalid JSON should get 0.0 reward"

    # Test case 4: Invalid tour (duplicate cities)
    invalid_tour = [0, 1, 1, 2, 3][:n_cities]
    while len(invalid_tour) < n_cities:
        invalid_tour.append(0)
    invalid_response = f'{{"tour": {invalid_tour}}}'
    state4 = state.copy()
    reward4 = await tsp_reward(invalid_response, "", state4)
    print(f"  Case 4 (invalid tour - duplicates): reward = {reward4:.4f}")
    assert reward4 == 0.0, "Invalid tour should get 0.0 reward"

    print("\n✓ All reward computations working correctly")

    # 5. Test with multiple instances
    print("\n[5/6] Testing across multiple instances...")
    all_valid = True
    for i, sample in enumerate(env.dataset):
        # Verify each instance has required fields
        required = ['n_cities', 'coordinates', 'distance_matrix', 'baseline_tour', 'baseline_length']
        for field in required:
            if field not in sample:
                print(f"  ✗ Instance {i} missing field: {field}")
                all_valid = False

        # Verify baseline tour is valid
        baseline = sample['baseline_tour']
        if set(baseline) != set(range(sample['n_cities'])):
            print(f"  ✗ Instance {i} has invalid baseline tour")
            all_valid = False

    if all_valid:
        print(f"✓ All {len(env.dataset)} instances valid")

    # 6. Verify environment is ready for vf-eval
    print("\n[6/6] Checking environment compatibility...")
    checks = [
        (hasattr(env, 'dataset'), "Has dataset"),
        (hasattr(env, 'eval_dataset'), "Has eval_dataset"),
        (hasattr(env, 'rubric'), "Has rubric"),
        (hasattr(env, 'rollout'), "Has rollout method"),
        (len(env.dataset) > 0, "Dataset not empty"),
        (len(env.eval_dataset) > 0, "Eval dataset not empty"),
    ]

    for check, desc in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {desc}")
        assert check, f"Failed: {desc}"

    print("\n" + "=" * 70)
    print("✓ ALL INTEGRATION TESTS PASSED")
    print("=" * 70)
    print("\nEnvironment is ready for:")
    print("  • vf-eval with real models")
    print("  • RL training with verifiers")
    print("  • Publication to Prime Intellect Hub")
    print("\nTo test with a model:")
    print("  export OPENAI_API_KEY=your-key")
    print("  uv run vf-eval tsp_rl_env -n 5 -r 1 -m gpt-3.5-turbo")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
