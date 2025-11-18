"""
TSP RL Environment for Prime Intellect Environment Hub

This module implements a Traveling Salesman Problem (TSP) environment
compatible with the Verifiers framework. All TSP instances are generated
synthetically from random seeds.
"""

import json
import random
from typing import Any

import numpy as np
import verifiers as vf
from datasets import Dataset


# =============================================================================
# TSP Instance Generation
# =============================================================================

def generate_tsp_instance(n_cities: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a TSP instance with random city coordinates and distance matrix.

    Args:
        n_cities: Number of cities
        seed: Random seed for coordinate generation

    Returns:
        Tuple of (coordinates, distance_matrix)
        - coordinates: (n_cities, 2) array of city positions in [0, 1]^2
        - distance_matrix: (n_cities, n_cities) array of Euclidean distances
    """
    rng = np.random.RandomState(seed)

    # Generate random coordinates in unit square
    coordinates = rng.uniform(0.0, 1.0, size=(n_cities, 2))

    # Compute pairwise distance matrix
    distance_matrix = np.zeros((n_cities, n_cities))
    for i in range(n_cities):
        for j in range(n_cities):
            if i != j:
                dx = coordinates[i, 0] - coordinates[j, 0]
                dy = coordinates[i, 1] - coordinates[j, 1]
                distance_matrix[i, j] = np.sqrt(dx**2 + dy**2)

    return coordinates, distance_matrix


# =============================================================================
# Baseline Heuristic
# =============================================================================

def nearest_neighbor_tour(distance_matrix: np.ndarray, start_city: int = 0) -> tuple[list[int], float]:
    """
    Compute a nearest neighbor heuristic tour starting from a given city.

    Args:
        distance_matrix: (n_cities, n_cities) array of distances
        start_city: Starting city index (default 0)

    Returns:
        Tuple of (tour, tour_length)
        - tour: List of city indices in visit order
        - tour_length: Total length of the tour
    """
    n_cities = len(distance_matrix)
    unvisited = set(range(n_cities))

    tour = [start_city]
    unvisited.remove(start_city)
    current = start_city

    while unvisited:
        # Find nearest unvisited city
        nearest = min(unvisited, key=lambda city: distance_matrix[current, city])
        tour.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    # Compute tour length (including return to start)
    tour_length = sum(
        distance_matrix[tour[i], tour[i + 1]] for i in range(n_cities - 1)
    )
    tour_length += distance_matrix[tour[-1], tour[0]]  # Return to start

    return tour, tour_length


# =============================================================================
# Tour Validation and Computation
# =============================================================================

def is_valid_tour(tour: list[int], n_cities: int) -> bool:
    """
    Check if a tour is a valid permutation of all cities.

    Args:
        tour: List of city indices
        n_cities: Expected number of cities

    Returns:
        True if tour is valid, False otherwise
    """
    if len(tour) != n_cities:
        return False

    if set(tour) != set(range(n_cities)):
        return False

    return True


def compute_tour_length(tour: list[int], distance_matrix: np.ndarray) -> float:
    """
    Compute the total length of a tour.

    Args:
        tour: List of city indices in visit order
        distance_matrix: (n_cities, n_cities) array of distances

    Returns:
        Total tour length including return to start
    """
    n_cities = len(tour)

    # Sum distances between consecutive cities
    tour_length = sum(
        distance_matrix[tour[i], tour[i + 1]] for i in range(n_cities - 1)
    )

    # Add return to start
    tour_length += distance_matrix[tour[-1], tour[0]]

    return tour_length


# =============================================================================
# Prompt Generation
# =============================================================================

def create_system_prompt() -> str:
    """
    Create the system prompt for the TSP environment.

    Returns:
        System prompt string
    """
    return """You are an expert algorithm designer solving Traveling Salesman Problem instances. You will be given N cities with coordinates in the plane. Your job is to output a single Hamiltonian tour that visits each city exactly once and returns to the starting city.

Output must be in strict JSON format, with no extra text.
Format:
{"tour": [0, 5, 2, 1, ...]}

where each integer is a city index and each city appears exactly once."""


def create_user_prompt(instance_id: int, n_cities: int, coordinates: np.ndarray) -> str:
    """
    Create the user prompt for a specific TSP instance.

    Args:
        instance_id: Instance identifier
        n_cities: Number of cities
        coordinates: (n_cities, 2) array of city positions

    Returns:
        User prompt string
    """
    lines = [
        f"Instance ID: {instance_id}",
        f"Number of cities: {n_cities}",
        "City coordinates:",
    ]

    for i in range(n_cities):
        x, y = coordinates[i]
        lines.append(f"- City {i}: ({x:.6f}, {y:.6f})")

    lines.append("")
    lines.append('Return only a valid JSON object of the form {"tour": [...]} as described in the system prompt. Do not include comments or explanation.')

    return "\n".join(lines)


# =============================================================================
# Parsing
# =============================================================================

def parse_tour_output(completion: str, n_cities: int) -> tuple[list[int] | None, dict[str, Any]]:
    """
    Parse the model's output to extract the tour.

    Args:
        completion: Model's completion text
        n_cities: Expected number of cities

    Returns:
        Tuple of (tour, metadata)
        - tour: List of city indices if valid, None if parsing failed
        - metadata: Dict with parsing information
    """
    metadata = {
        "parse_success": False,
        "parse_error": None,
        "validation_error": None,
    }

    try:
        # Try to parse JSON
        data = json.loads(completion.strip())

        if "tour" not in data:
            metadata["parse_error"] = "Missing 'tour' field in JSON"
            return None, metadata

        tour = data["tour"]

        if not isinstance(tour, list):
            metadata["parse_error"] = "'tour' field is not a list"
            return None, metadata

        # Convert to integers
        try:
            tour = [int(x) for x in tour]
        except (ValueError, TypeError) as e:
            metadata["parse_error"] = f"Tour contains non-integer values: {e}"
            return None, metadata

        # Validate tour
        if not is_valid_tour(tour, n_cities):
            metadata["validation_error"] = "Tour is not a valid permutation of cities"
            return None, metadata

        metadata["parse_success"] = True
        return tour, metadata

    except json.JSONDecodeError as e:
        metadata["parse_error"] = f"JSON parsing failed: {e}"
        return None, metadata


# =============================================================================
# Dataset Generation
# =============================================================================

def generate_synthetic_dataset(
    num_examples: int,
    min_cities: int,
    max_cities: int,
    dataset_seed: int,
) -> Dataset:
    """
    Generate a synthetic TSP dataset with pre-computed instances and prompts.

    Args:
        num_examples: Number of TSP instances to generate
        min_cities: Minimum number of cities per instance
        max_cities: Maximum number of cities per instance
        dataset_seed: Random seed for reproducibility

    Returns:
        HuggingFace Dataset with all instance data and prompts
    """
    rng = random.Random(dataset_seed)

    data = []
    for i in range(num_examples):
        n_cities = rng.randint(min_cities, max_cities)
        instance_seed = rng.randint(0, 2**31 - 1)

        # Generate TSP instance
        coordinates, distance_matrix = generate_tsp_instance(n_cities, instance_seed)

        # Compute baseline tour
        baseline_tour, baseline_length = nearest_neighbor_tour(distance_matrix)

        # Create prompt
        question = create_user_prompt(i, n_cities, coordinates)

        # Store all data needed for evaluation
        data.append({
            "instance_id": i,
            "n_cities": n_cities,
            "seed": instance_seed,
            "question": question,  # This will be auto-formatted into prompt
            "coordinates": coordinates.tolist(),  # Store as list for JSON serialization
            "distance_matrix": distance_matrix.tolist(),
            "baseline_tour": baseline_tour,
            "baseline_length": float(baseline_length),
            "answer": "",  # TSP has no single correct answer
        })

    return Dataset.from_list(data)


# =============================================================================
# Reward Function
# =============================================================================

async def tsp_reward(
    completion: str,
    answer: Any,
    state: vf.State,
    **kwargs
) -> float:
    """
    Compute reward for a TSP tour completion.

    The reward is based on:
    1. Validity: Output must parse correctly and be a valid tour
    2. Quality: Tour length compared to nearest neighbor baseline

    Args:
        completion: Model's completion text
        answer: Ground truth answer (unused, TSP has no single answer)
        state: Verifiers state object containing instance data
        **kwargs: Additional arguments

    Returns:
        Reward in [0.0, 1.0]
    """
    # Get instance data from state (stored from dataset row)
    n_cities = state["info"]["n_cities"]
    coordinates = np.array(state["info"]["coordinates"])
    distance_matrix = np.array(state["info"]["distance_matrix"])
    baseline_length = state["info"]["baseline_length"]

    # Parse the tour
    tour, metadata = parse_tour_output(completion, n_cities)

    # Store parsing metadata in state for debugging
    state["parse_metadata"] = metadata

    if tour is None:
        # Parsing or validation failed
        return 0.0

    # Compute tour length
    model_length = compute_tour_length(tour, distance_matrix)

    # Store tour info in state
    state["model_tour"] = tour
    state["model_tour_length"] = model_length
    state["improvement"] = baseline_length - model_length

    # Compute normalized quality reward
    # Reward = max(0, (baseline - model) / baseline)
    # This gives positive reward when model beats baseline
    if baseline_length > 0:
        quality_reward = max(0.0, (baseline_length - model_length) / baseline_length)
    else:
        # Edge case: if baseline is 0, model should also be 0
        quality_reward = 1.0 if model_length == 0 else 0.0

    # Clamp to [0, 1]
    quality_reward = min(1.0, max(0.0, quality_reward))

    return quality_reward


# =============================================================================
# Main Environment Function
# =============================================================================

def load_environment(
    num_examples: int = 128,
    eval_num_examples: int | None = None,
    min_cities: int = 10,
    max_cities: int = 30,
    dataset_seed: int = 42,
    system_prompt: str | None = None,
    **kwargs
) -> vf.Environment:
    """
    Load the TSP RL environment.

    This environment generates synthetic Traveling Salesman Problem instances
    and evaluates model-generated tours based on their quality relative to
    a nearest neighbor baseline.

    Args:
        num_examples: Number of training examples (default 128)
        eval_num_examples: Number of eval examples (default: same as num_examples)
        min_cities: Minimum number of cities per instance (default 10)
        max_cities: Maximum number of cities per instance (default 30)
        dataset_seed: Random seed for dataset generation (default 42)
        system_prompt: Custom system prompt (default: use built-in prompt)
        **kwargs: Additional arguments (ignored)

    Returns:
        Verifiers Environment object
    """
    # Handle defaults
    if eval_num_examples is None:
        eval_num_examples = num_examples

    if system_prompt is None:
        system_prompt = create_system_prompt()

    # Generate synthetic datasets with all instance data pre-computed
    dataset = generate_synthetic_dataset(
        num_examples=num_examples,
        min_cities=min_cities,
        max_cities=max_cities,
        dataset_seed=dataset_seed,
    )

    eval_dataset = generate_synthetic_dataset(
        num_examples=eval_num_examples,
        min_cities=min_cities,
        max_cities=max_cities,
        dataset_seed=dataset_seed + 1000,  # Different seed for eval
    )

    # Create rubric with TSP reward function
    rubric = vf.Rubric(
        funcs=[tsp_reward],
        weights=[1.0],
    )

    # Create environment
    env = vf.SingleTurnEnv(
        dataset=dataset,
        eval_dataset=eval_dataset,
        system_prompt=system_prompt,
        rubric=rubric,
    )

    return env
