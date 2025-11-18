"""
Unit tests for TSP RL Environment

Tests cover:
- Dataset generation
- TSP instance generation
- Tour validation
- Reward computation
- Parsing
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

# Add parent directory to path to import tsp_rl_env
sys.path.insert(0, str(Path(__file__).parent.parent / "environments" / "tsp_rl_env"))

from tsp_rl_env import (
    generate_synthetic_dataset,
    generate_tsp_instance,
    nearest_neighbor_tour,
    is_valid_tour,
    compute_tour_length,
    parse_tour_output,
    create_system_prompt,
    create_user_prompt,
)


class TestDatasetGeneration:
    """Test synthetic dataset generation"""

    def test_dataset_size(self):
        """Test that dataset has correct number of examples"""
        dataset = generate_synthetic_dataset(
            num_examples=10,
            min_cities=5,
            max_cities=15,
            dataset_seed=42,
        )
        assert len(dataset) == 10

    def test_dataset_columns(self):
        """Test that dataset has expected columns"""
        dataset = generate_synthetic_dataset(
            num_examples=5,
            min_cities=5,
            max_cities=15,
            dataset_seed=42,
        )
        row = dataset[0]
        assert "instance_id" in row
        assert "n_cities" in row
        assert "seed" in row
        assert "question" in row
        assert "coordinates" in row
        assert "distance_matrix" in row
        assert "baseline_tour" in row
        assert "baseline_length" in row

    def test_dataset_city_range(self):
        """Test that number of cities is within specified range"""
        dataset = generate_synthetic_dataset(
            num_examples=20,
            min_cities=10,
            max_cities=30,
            dataset_seed=42,
        )
        for row in dataset:
            assert 10 <= row["n_cities"] <= 30

    def test_dataset_reproducibility(self):
        """Test that same seed produces same dataset"""
        ds1 = generate_synthetic_dataset(10, 5, 15, 42)
        ds2 = generate_synthetic_dataset(10, 5, 15, 42)

        for i in range(10):
            assert ds1[i]["n_cities"] == ds2[i]["n_cities"]
            assert ds1[i]["seed"] == ds2[i]["seed"]


class TestTSPInstanceGeneration:
    """Test TSP instance generation"""

    def test_coordinates_shape(self):
        """Test that coordinates have correct shape"""
        coords, dist_matrix = generate_tsp_instance(n_cities=10, seed=42)
        assert coords.shape == (10, 2)

    def test_coordinates_range(self):
        """Test that coordinates are in [0, 1]"""
        coords, _ = generate_tsp_instance(n_cities=20, seed=42)
        assert np.all(coords >= 0.0)
        assert np.all(coords <= 1.0)

    def test_distance_matrix_shape(self):
        """Test that distance matrix has correct shape"""
        _, dist_matrix = generate_tsp_instance(n_cities=15, seed=42)
        assert dist_matrix.shape == (15, 15)

    def test_distance_matrix_symmetric(self):
        """Test that distance matrix is symmetric"""
        _, dist_matrix = generate_tsp_instance(n_cities=10, seed=42)
        assert np.allclose(dist_matrix, dist_matrix.T)

    def test_distance_matrix_diagonal(self):
        """Test that diagonal is zero (distance to self)"""
        _, dist_matrix = generate_tsp_instance(n_cities=10, seed=42)
        assert np.allclose(np.diag(dist_matrix), 0.0)

    def test_reproducibility(self):
        """Test that same seed produces same instance"""
        coords1, dist1 = generate_tsp_instance(10, 42)
        coords2, dist2 = generate_tsp_instance(10, 42)

        assert np.allclose(coords1, coords2)
        assert np.allclose(dist1, dist2)


class TestNearestNeighbor:
    """Test nearest neighbor heuristic"""

    def test_tour_length(self):
        """Test that tour visits all cities"""
        _, dist_matrix = generate_tsp_instance(n_cities=10, seed=42)
        tour, length = nearest_neighbor_tour(dist_matrix)
        assert len(tour) == 10

    def test_tour_validity(self):
        """Test that tour is a valid permutation"""
        _, dist_matrix = generate_tsp_instance(n_cities=10, seed=42)
        tour, _ = nearest_neighbor_tour(dist_matrix)
        assert set(tour) == set(range(10))
        assert len(tour) == len(set(tour))  # No duplicates

    def test_tour_starts_at_zero(self):
        """Test that tour starts at city 0"""
        _, dist_matrix = generate_tsp_instance(n_cities=10, seed=42)
        tour, _ = nearest_neighbor_tour(dist_matrix)
        assert tour[0] == 0

    def test_length_positive(self):
        """Test that tour length is positive"""
        _, dist_matrix = generate_tsp_instance(n_cities=10, seed=42)
        _, length = nearest_neighbor_tour(dist_matrix)
        assert length > 0

    def test_length_computation(self):
        """Test that tour length is computed correctly"""
        _, dist_matrix = generate_tsp_instance(n_cities=5, seed=42)
        tour, length = nearest_neighbor_tour(dist_matrix)

        # Manually compute length
        manual_length = 0.0
        for i in range(len(tour) - 1):
            manual_length += dist_matrix[tour[i], tour[i + 1]]
        manual_length += dist_matrix[tour[-1], tour[0]]  # Return edge

        assert np.isclose(length, manual_length)


class TestTourValidation:
    """Test tour validation functions"""

    def test_valid_tour(self):
        """Test that valid tour is recognized"""
        tour = [0, 1, 2, 3, 4]
        assert is_valid_tour(tour, 5)

    def test_valid_tour_different_order(self):
        """Test that permutation order doesn't matter"""
        tour = [2, 0, 4, 1, 3]
        assert is_valid_tour(tour, 5)

    def test_invalid_tour_wrong_length(self):
        """Test that wrong length is rejected"""
        tour = [0, 1, 2]
        assert not is_valid_tour(tour, 5)

    def test_invalid_tour_duplicate(self):
        """Test that duplicates are rejected"""
        tour = [0, 1, 2, 2, 3]
        assert not is_valid_tour(tour, 5)

    def test_invalid_tour_missing_city(self):
        """Test that missing cities are rejected"""
        tour = [0, 1, 2, 3, 5]  # Missing 4, has 5
        assert not is_valid_tour(tour, 6)

    def test_tour_length_computation(self):
        """Test tour length computation"""
        # Create simple instance
        coords = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0],
        ])

        # Compute distance matrix
        n = len(coords)
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    dx = coords[i, 0] - coords[j, 0]
                    dy = coords[i, 1] - coords[j, 1]
                    dist_matrix[i, j] = np.sqrt(dx**2 + dy**2)

        # Tour around square: 0 -> 1 -> 2 -> 3 -> 0
        tour = [0, 1, 2, 3]
        length = compute_tour_length(tour, dist_matrix)

        # Length should be 4.0 (perimeter of unit square)
        assert np.isclose(length, 4.0)


class TestParsing:
    """Test output parsing"""

    def test_parse_valid_output(self):
        """Test parsing of valid JSON output"""
        output = '{"tour": [0, 1, 2, 3, 4]}'
        tour, metadata = parse_tour_output(output, n_cities=5)

        assert tour is not None
        assert tour == [0, 1, 2, 3, 4]
        assert metadata["parse_success"]

    def test_parse_valid_with_whitespace(self):
        """Test parsing with extra whitespace"""
        output = '  {"tour": [0, 1, 2, 3, 4]}  \n'
        tour, metadata = parse_tour_output(output, n_cities=5)

        assert tour is not None
        assert tour == [0, 1, 2, 3, 4]

    def test_parse_invalid_json(self):
        """Test parsing of invalid JSON"""
        output = 'not json'
        tour, metadata = parse_tour_output(output, n_cities=5)

        assert tour is None
        assert not metadata["parse_success"]
        assert metadata["parse_error"] is not None

    def test_parse_missing_tour_field(self):
        """Test parsing when tour field is missing"""
        output = '{"solution": [0, 1, 2, 3, 4]}'
        tour, metadata = parse_tour_output(output, n_cities=5)

        assert tour is None
        assert "Missing 'tour'" in metadata["parse_error"]

    def test_parse_invalid_tour_type(self):
        """Test parsing when tour is not a list"""
        output = '{"tour": "0,1,2,3,4"}'
        tour, metadata = parse_tour_output(output, n_cities=5)

        assert tour is None
        assert "'tour' field is not a list" in metadata["parse_error"]

    def test_parse_invalid_permutation(self):
        """Test parsing when tour is not valid permutation"""
        output = '{"tour": [0, 1, 2, 2, 3]}'  # Duplicate
        tour, metadata = parse_tour_output(output, n_cities=5)

        assert tour is None
        assert metadata["validation_error"] is not None

    def test_parse_non_integer_values(self):
        """Test parsing when tour contains non-integers"""
        output = '{"tour": [0, 1, 2, 3, "four"]}'
        tour, metadata = parse_tour_output(output, n_cities=5)

        assert tour is None
        assert "non-integer" in metadata["parse_error"].lower()


class TestPromptGeneration:
    """Test prompt generation"""

    def test_system_prompt_not_empty(self):
        """Test that system prompt is generated"""
        prompt = create_system_prompt()
        assert len(prompt) > 0
        assert "Traveling Salesman" in prompt or "TSP" in prompt.upper()
        assert "JSON" in prompt.upper()

    def test_user_prompt_contains_coords(self):
        """Test that user prompt contains coordinates"""
        coords = np.array([
            [0.1, 0.2],
            [0.3, 0.4],
            [0.5, 0.6],
        ])
        prompt = create_user_prompt(instance_id=42, n_cities=3, coordinates=coords)

        assert "Instance ID: 42" in prompt or "42" in prompt
        assert "3" in prompt
        assert "0.1" in prompt or "0.10" in prompt
        assert "0.2" in prompt or "0.20" in prompt

    def test_user_prompt_all_cities(self):
        """Test that all cities are included in prompt"""
        coords = np.array([
            [0.1, 0.2],
            [0.3, 0.4],
            [0.5, 0.6],
            [0.7, 0.8],
        ])
        prompt = create_user_prompt(instance_id=0, n_cities=4, coordinates=coords)

        for i in range(4):
            assert f"City {i}" in prompt or f"{i}" in prompt


class TestIntegration:
    """Integration tests"""

    def test_full_pipeline(self):
        """Test full pipeline from dataset to reward"""
        # Generate dataset
        dataset = generate_synthetic_dataset(
            num_examples=2,
            min_cities=5,
            max_cities=10,
            dataset_seed=42,
        )

        # Get first instance
        row = dataset[0]
        n_cities = row["n_cities"]
        seed = row["seed"]

        # Generate TSP instance
        coords, dist_matrix = generate_tsp_instance(n_cities, seed)

        # Compute baseline
        baseline_tour, baseline_length = nearest_neighbor_tour(dist_matrix)

        # Check baseline is valid
        assert is_valid_tour(baseline_tour, n_cities)

        # Create a tour that just reverses baseline (likely different quality)
        test_tour = list(reversed(baseline_tour))
        test_length = compute_tour_length(test_tour, dist_matrix)

        # Both should be valid tours
        assert is_valid_tour(test_tour, n_cities)
        assert test_length > 0
        assert baseline_length > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
