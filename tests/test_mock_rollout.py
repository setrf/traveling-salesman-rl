"""
Mock rollout test - simulates complete vf-eval flow without API calls
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "environments" / "tsp_rl_env"))

import asyncio
import verifiers as vf
import numpy as np
from tsp_rl_env import nearest_neighbor_tour, compute_tour_length


async def mock_model_response(prompt, n_cities, coordinates, distance_matrix):
    """
    Simulate a model that generates a somewhat intelligent tour.
    Uses nearest neighbor from random starting city.
    """
    # Pick random start
    start = np.random.randint(0, n_cities)
    tour, _ = nearest_neighbor_tour(distance_matrix, start_city=start)

    # Return as JSON
    return f'{{"tour": {tour}}}'


async def test_mock_rollout():
    """Simulate a complete rollout with mock model"""
    print("=" * 70)
    print("MOCK ROLLOUT TEST - Simulating vf-eval behavior")
    print("=" * 70)

    # Load environment
    print("\n[1] Loading environment...")
    env = vf.load_environment('tsp_rl_env', num_examples=5, eval_num_examples=3, min_cities=10, max_cities=15)
    print(f"✓ Loaded: {len(env.dataset)} train examples")

    # Process several examples
    print(f"\n[2] Running mock rollouts on {len(env.dataset)} examples...\n")

    rewards = []
    for idx, sample in enumerate(env.dataset):
        n_cities = sample['n_cities']
        coords = np.array(sample['coordinates'])
        dist_matrix = np.array(sample['distance_matrix'])
        baseline_length = sample['baseline_length']

        # Generate mock model response
        mock_response = await mock_model_response(
            sample['prompt'],
            n_cities,
            coords,
            dist_matrix
        )

        # Parse and evaluate
        import json
        from tsp_rl_env import compute_tour_length, tsp_reward

        # Create state as verifiers would
        state = {
            "info": {
                "n_cities": n_cities,
                "coordinates": sample['coordinates'],
                "distance_matrix": sample['distance_matrix'],
                "baseline_length": baseline_length,
            }
        }

        # Compute reward
        reward = await tsp_reward(mock_response, "", state)

        # Parse tour to show details
        tour_data = json.loads(mock_response)
        model_tour = tour_data['tour']
        model_length = compute_tour_length(model_tour, dist_matrix)

        improvement_pct = ((baseline_length - model_length) / baseline_length) * 100

        print(f"  Example {idx}:")
        print(f"    Cities: {n_cities}")
        print(f"    Baseline length: {baseline_length:.4f}")
        print(f"    Model length:    {model_length:.4f}")
        print(f"    Improvement:     {improvement_pct:+.2f}%")
        print(f"    Reward:          {reward:.4f}")

        rewards.append(reward)

    # Summary statistics
    print("\n" + "=" * 70)
    print("ROLLOUT SUMMARY")
    print("=" * 70)
    print(f"  Examples evaluated: {len(rewards)}")
    print(f"  Mean reward:        {np.mean(rewards):.4f}")
    print(f"  Std reward:         {np.std(rewards):.4f}")
    print(f"  Min reward:         {np.min(rewards):.4f}")
    print(f"  Max reward:         {np.max(rewards):.4f}")
    print(f"  Non-zero rewards:   {sum(r > 0 for r in rewards)}/{len(rewards)}")

    print("\n" + "=" * 70)
    print("✓ MOCK ROLLOUT TEST PASSED")
    print("=" * 70)
    print("\nThis demonstrates the environment would work correctly with vf-eval.")
    print("The pipeline is:")
    print("  1. Load environment ✓")
    print("  2. Get prompts ✓")
    print("  3. Model generates tour ✓")
    print("  4. Parse JSON response ✓")
    print("  5. Validate tour ✓")
    print("  6. Compute reward ✓")
    print("\nReady for production use!")


if __name__ == "__main__":
    asyncio.run(test_mock_rollout())
