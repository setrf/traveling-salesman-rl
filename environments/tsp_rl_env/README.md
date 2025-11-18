# TSP RL Environment

**Environment ID**: `tsp-rl-env`

A Traveling Salesman Problem (TSP) environment for reinforcement learning training and evaluation, compatible with Verifiers and Prime Intellect's Environment Hub.

## Overview

This environment provides synthetically generated Euclidean TSP instances in the unit square [0, 1] × [0, 1]. It is designed for:

- **RL Training**: Train models to generate high-quality tours with verifiable rewards
- **Evaluation**: Benchmark model performance against a nearest neighbor baseline
- **Research**: Study optimization capabilities in language models

All instances are generated from random seeds - no external data is required.

## Task Definition

### The Traveling Salesman Problem

Given N cities with 2D coordinates in the unit square [0, 1] × [0, 1], find the shortest Hamiltonian tour that:

1. Visits each city exactly once
2. Returns to the starting city
3. Minimizes the total Euclidean distance traveled

### Instance Generation

Each TSP instance is generated synthetically:

- **Coordinates**: N random points uniformly sampled from [0, 1] × [0, 1]
- **Distances**: Euclidean distance between all city pairs
- **Reproducibility**: Each instance uses a unique random seed for deterministic generation

### Problem Characteristics

- **Instance Size**: Configurable between 10-30 cities (default)
- **Distance Metric**: Euclidean (L2) distance in 2D plane
- **Tour Representation**: Permutation of city indices [0, 1, ..., N-1]
- **Tour Length**: Sum of edge distances plus return edge

## Input and Output Formats

### System Prompt

The model receives a constant system prompt explaining the task:

```
You are an expert algorithm designer solving Traveling Salesman Problem instances.
You will be given N cities with coordinates in the plane. Your job is to output
a single Hamiltonian tour that visits each city exactly once and returns to the
starting city.

Output must be in strict JSON format, with no extra text.
Format:
{"tour": [0, 5, 2, 1, ...]}

where each integer is a city index and each city appears exactly once.
```

### User Prompt (Per Instance)

Each instance includes:

```
Instance ID: 42
Number of cities: 15
City coordinates:
- City 0: (0.123456, 0.789012)
- City 1: (0.345678, 0.901234)
...
- City 14: (0.567890, 0.123456)

Return only a valid JSON object of the form {"tour": [...]} as described
in the system prompt. Do not include comments or explanation.
```

### Required Output Format

The model must output a JSON object:

```json
{"tour": [0, 5, 2, 1, 3, 4, ...]}
```

**Validity Requirements**:
- `tour` must be a list of integers
- Length must equal the number of cities
- Must be a permutation of all city indices (0 to N-1)
- No duplicates, no missing cities

## Reward Function

The reward function evaluates tour quality with two components:

### 1. Validity Check

- **Invalid outputs** (parsing errors, missing fields, malformed tours): `reward = 0.0`
- **Valid outputs**: Proceed to quality evaluation

### 2. Quality Reward

Tours are scored relative to a **nearest neighbor baseline**:

```
baseline_tour = nearest_neighbor_heuristic(instance)
baseline_length = compute_tour_length(baseline_tour)
model_length = compute_tour_length(model_tour)

quality_reward = max(0.0, (baseline_length - model_length) / baseline_length)
```

**Interpretation**:
- `reward = 0.0`: Model tour is worse than or equal to baseline
- `reward > 0.0`: Model tour is better than baseline
- `reward = 1.0`: Model tour is twice as short as baseline (or better)

**Total Reward**: `reward ∈ [0.0, 1.0]`

### Nearest Neighbor Baseline

The baseline is a simple greedy heuristic:

1. Start at city 0
2. At each step, visit the nearest unvisited city
3. Return to city 0 after visiting all cities

This provides a reasonable but suboptimal reference tour. Most small TSP instances can be improved beyond this baseline with better algorithms.

## Environment Configuration

Configure the environment using arguments to `load_environment()` or via `pyproject.toml`:

### Environment Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `num_examples` | int | 128 | Number of training instances |
| `eval_num_examples` | int | 32 | Number of evaluation instances |
| `min_cities` | int | 10 | Minimum cities per instance |
| `max_cities` | int | 30 | Maximum cities per instance |
| `dataset_seed` | int | 42 | Random seed for dataset generation |
| `system_prompt` | str | (default) | Custom system prompt (optional) |

### Example Configuration

```python
import verifiers as vf

env = vf.load_environment(
    'tsp_rl_env',
    num_examples=256,
    eval_num_examples=64,
    min_cities=15,
    max_cities=25,
    dataset_seed=123,
)
```

## Usage

### Local Installation

From the repository root:

```bash
cd environments/tsp_rl_env
uv pip install -e .
```

Or install directly:

```bash
uv pip install -e environments/tsp_rl_env
```

### Quick Evaluation

Run a quick evaluation with default settings:

```bash
uv run vf-eval tsp_rl_env
```

This will evaluate 5 examples with 3 rollouts each (configurable in `pyproject.toml`).

### Configuring Evaluation

Specify model, number of examples, and environment arguments:

```bash
uv run vf-eval tsp_rl_env \
  -m gpt-4.1-mini \
  -n 20 \
  -r 5 \
  -t 1024 \
  -T 0.7 \
  -a '{"min_cities": 15, "max_cities": 25}'
```

**Flags**:
- `-m`: Model name
- `-n`: Number of examples
- `-r`: Rollouts per example
- `-t`: Max tokens per completion
- `-T`: Temperature
- `-a`: Environment arguments as JSON

### Publishing to Prime Intellect Hub

After logging in to Prime:

```bash
prime login
```

Publish the environment:

```bash
cd environments/tsp_rl_env
prime env push
```

**Optional flags**:
- `--visibility PRIVATE`: Make environment private
- `--team <team-name>`: Publish under team account

### Evaluation on Prime Hub

After publishing, run evaluations on Prime's infrastructure:

```bash
prime env eval <owner>/tsp-rl-env \
  -m meta-llama/llama-3.1-70b-instruct \
  -n 32 \
  -r 3
```

## Metrics

The environment tracks the following metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `reward` | float | Main scalar reward (quality vs baseline) |
| `parse_success` | bool | Whether output was valid JSON |
| `model_tour_length` | float | Total length of model's tour |
| `baseline_tour_length` | float | Total length of baseline tour |
| `improvement_pct` | float | `(baseline - model) / baseline * 100` |

Additional state information (stored but not returned as metrics):
- `coordinates`: City positions
- `distance_matrix`: Pairwise distances
- `baseline_tour`: Baseline tour sequence
- `model_tour`: Model's tour sequence
- `parse_metadata`: Detailed parsing information

## RL Training Notes

This environment is suitable for RL training with `prime-rl` or any Verifiers-compatible RL framework:

### Single Turn Environment

- **Interaction**: One prompt in, one complete tour out
- **No partial feedback**: Model must generate full solution in one response
- **Verifiable rewards**: Reward is deterministic given a tour

### Training Considerations

1. **Curriculum Learning**: Start with smaller instances (`min_cities=10, max_cities=15`), gradually increase
2. **Exploration**: Use temperature > 0 to explore different tours
3. **Format Adherence**: Models must learn strict JSON format to receive non-zero rewards
4. **Baseline Difficulty**: Nearest neighbor is easy to beat for small instances, harder for larger ones

### Expected Performance

- **Untrained LLMs**: May struggle with format or produce invalid permutations
- **After format training**: Should reliably produce valid tours
- **After RL training**: Should consistently beat nearest neighbor baseline
- **Strong performance**: 10-30% improvement over baseline on average

## Example Interaction

**System Prompt**:
```
You are an expert algorithm designer solving Traveling Salesman Problem instances...
[full prompt]
```

**User Prompt**:
```
Instance ID: 0
Number of cities: 5
City coordinates:
- City 0: (0.374540, 0.950714)
- City 1: (0.731994, 0.598658)
- City 2: (0.156019, 0.155995)
- City 3: (0.058084, 0.866176)
- City 4: (0.601115, 0.708073)

Return only a valid JSON object...
```

**Model Output**:
```json
{"tour": [0, 3, 2, 1, 4]}
```

**Evaluation**:
- Parse: ✓ Valid JSON
- Validity: ✓ Valid permutation
- Model tour length: 2.834
- Baseline tour length: 3.012
- Reward: `(3.012 - 2.834) / 3.012 = 0.059` (5.9% improvement)

## Development and Testing

### Running Tests

```bash
pytest tests/test_tsp_rl_env.py
```

### Importing Programmatically

```python
import verifiers as vf

# Load environment
env = vf.load_environment('tsp_rl_env')

# Access dataset
print(f"Training examples: {len(env.dataset)}")
print(f"Eval examples: {len(env.eval_dataset)}")

# Get an example
row = env.dataset[0]
print(f"Instance {row['instance_id']}: {row['n_cities']} cities")
```

## Contributing

To extend or modify this environment:

1. Edit `tsp_rl_env.py` for core logic
2. Update `pyproject.toml` for dependencies or metadata
3. Run tests to verify changes
4. Update this README if behavior changes

## License

This environment is part of the traveling-salesman-rl repository.

## References

- [Prime Intellect Environment Docs](https://docs.primeintellect.ai/verifiers/environments)
- [Verifiers Documentation](https://github.com/PrimeIntellect-ai/verifiers)
- [Classic TSP on Wikipedia](https://en.wikipedia.org/wiki/Travelling_salesman_problem)

## Support

For issues or questions:
- Open an issue in the repository
- Check Prime Intellect documentation
- Review Verifiers examples

---

**Version**: 0.1.0
**Last Updated**: 2025-11-18
