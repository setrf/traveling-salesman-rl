# Traveling Salesman RL Environment

This repository contains a **Traveling Salesman Problem (TSP)** environment for reinforcement learning training and evaluation, compatible with [Verifiers](https://github.com/PrimeIntellect-ai/verifiers) and [Prime Intellect's Environment Hub](https://docs.primeintellect.ai/).

## Overview

The TSP environment provides synthetically generated Euclidean TSP instances for:
- **RL Training**: Train language models to generate high-quality tours
- **Evaluation**: Benchmark model performance against heuristic baselines
- **Research**: Study optimization capabilities in foundation models

All instances are generated from random seeds - no external data required.

## Quick Start

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-org/traveling-salesman-rl.git
   cd traveling-salesman-rl
   ```

2. Create a virtual environment and install the TSP environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e environments/tsp_rl_env
   ```

### Local Evaluation

Run a quick evaluation with Verifiers:

```bash
source .venv/bin/activate
uv run vf-eval tsp_rl_env -n 5 -r 1
```

This evaluates the environment on 5 examples with 1 rollout each using the default model.

### Publishing to Prime Intellect Hub

1. Authenticate with Prime:
   ```bash
   prime login
   ```

2. Push the environment:
   ```bash
   cd environments/tsp_rl_env
   prime env push
   ```

3. Run evaluation on Prime's infrastructure:
   ```bash
   prime env eval <owner>/tsp-rl-env -m meta-llama/llama-3.1-70b-instruct -n 32 -r 3
   ```

## Repository Structure

```
traveling-salesman-rl/
├── README.md                      # This file
├── DEV_NOTES_TSP_ENV.md           # Development notes and planning
├── environments/
│   └── tsp_rl_env/
│       ├── tsp_rl_env.py          # Main environment implementation
│       ├── pyproject.toml         # Package metadata and dependencies
│       └── README.md              # Detailed environment documentation
└── tests/
    └── test_tsp_rl_env.py         # Unit tests
```

## Environment Details

### Task: Traveling Salesman Problem

Given N cities with 2D coordinates in the unit square [0, 1] × [0, 1], find the shortest Hamiltonian tour that:
1. Visits each city exactly once
2. Returns to the starting city
3. Minimizes total Euclidean distance

### Input Format

Models receive city coordinates and must output a JSON tour:

**Input:**
```
Instance ID: 42
Number of cities: 15
City coordinates:
- City 0: (0.123456, 0.789012)
- City 1: (0.345678, 0.901234)
...
```

**Required Output:**
```json
{"tour": [0, 5, 2, 1, 3, 4, ...]}
```

### Reward Function

Tours are scored based on quality relative to a **nearest neighbor baseline**:

```
reward = max(0.0, (baseline_length - model_length) / baseline_length)
```

- `reward = 0.0`: Model tour is worse than or equal to baseline
- `reward > 0.0`: Model tour beats baseline
- `reward ∈ [0.0, 1.0]`: Normalized quality score

### Configuration

The environment supports several configuration parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_examples` | 128 | Number of training instances |
| `eval_num_examples` | 32 | Number of evaluation instances |
| `min_cities` | 10 | Minimum cities per instance |
| `max_cities` | 30 | Maximum cities per instance |
| `dataset_seed` | 42 | Random seed for reproducibility |

Example:
```python
import verifiers as vf

env = vf.load_environment(
    'tsp_rl_env',
    num_examples=256,
    min_cities=15,
    max_cities=25,
)
```

## Development

### Running Tests

```bash
source .venv/bin/activate
pytest tests/test_tsp_rl_env.py -v
```

### Testing the Environment

```bash
# Load and inspect
python -c "import verifiers as vf; env = vf.load_environment('tsp_rl_env'); print(f'Loaded {len(env.dataset)} examples')"

# Run evaluation
uv run vf-eval tsp_rl_env -n 5 -r 1
```

## Features

- **Synthetic Data**: All instances generated from random seeds
- **Verifiable Rewards**: Deterministic scoring based on tour quality
- **Configurable Difficulty**: Adjustable number of cities
- **Single Turn**: Complete tour in one model response
- **Baseline Comparison**: Nearest neighbor heuristic for normalization

## Use Cases

1. **RL Training**: Train models to solve optimization problems
2. **Prompting Research**: Study how different prompts affect tour quality
3. **Model Comparison**: Benchmark different models on combinatorial optimization
4. **Curriculum Learning**: Start with small instances, gradually increase difficulty

## Documentation

- **Environment README**: See `environments/tsp_rl_env/README.md` for detailed documentation
- **Development Notes**: See `DEV_NOTES_TSP_ENV.md` for implementation details
- **Prime Docs**: https://docs.primeintellect.ai/verifiers/environments
- **Verifiers Docs**: https://github.com/PrimeIntellect-ai/verifiers

## Requirements

- Python 3.10+
- `uv` package manager
- `verifiers` framework
- `prime` CLI (for publishing)

## License

MIT License - See LICENSE file for details

## Citation

If you use this environment in your research, please cite:

```bibtex
@software{tsp_rl_env,
  title = {TSP RL Environment for Prime Intellect},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/your-org/traveling-salesman-rl}
}
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues or questions:
- Open an issue in this repository
- Check Prime Intellect documentation
- Review Verifiers examples

---

**Status**: Ready for publication to Prime Intellect Environment Hub ✓

**Version**: 0.1.0
**Last Updated**: 2025-11-18
