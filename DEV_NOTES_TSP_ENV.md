# TSP RL Environment Development Notes

## Overview

Creating a Traveling Salesman Problem (TSP) environment for Prime Intellect's Environment Hub and Verifiers framework.

## Goals

1. **Single Turn RL Environment**: Model outputs complete tour in one response
2. **Synthetic Data Only**: All TSP instances generated from random seeds
3. **Verifiers Compatible**: Follows Verifiers environment spec
4. **Hub Ready**: Can be pushed with `prime env push`

## Environment Specification

### Name
- Package name: `tsp_rl_env`
- Hub name: `<owner>/tsp-rl-env`

### TSP Variant
- **Euclidean TSP** in unit square [0, 1] × [0, 1]
- N cities with random coordinates
- Tour is a permutation visiting all cities exactly once, returning to start
- Objective: Minimize total tour length (sum of Euclidean distances)

### Dataset Design
- **Synthetic generation** at environment load time
- Configurable parameters:
  - `num_examples`: Number of training instances (default 128)
  - `eval_num_examples`: Number of eval instances (default 32)
  - `min_cities`: Minimum cities per instance (default 10)
  - `max_cities`: Maximum cities per instance (default 30)
  - `dataset_seed`: Master seed for reproducibility (default 42)

- **Dataset schema**:
  - `instance_id`: Integer index
  - `n_cities`: Number of cities for this instance
  - `seed`: Random seed for coordinate generation
  - `comment`: Optional description

### Input Format (Prompt)

**System Prompt** (constant):
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

**User Prompt** (per instance):
```
Instance ID: {instance_id}
Number of cities: {n_cities}
City coordinates:
- City 0: ({x0}, {y0})
- City 1: ({x1}, {y1})
...
- City {n-1}: ({xn-1}, {yn-1})

Return only a valid JSON object of the form {"tour": [...]} as described
in the system prompt. Do not include comments or explanation.
```

### Output Format
- JSON object: `{"tour": [0, 5, 2, 1, ...]}`
- `tour` must be a permutation of `0, 1, ..., n_cities-1`
- No duplicates, no missing cities

### Reward Function

**Components**:

1. **Validity Check**:
   - If JSON parsing fails → reward = 0.0
   - If tour is not a valid permutation → reward = 0.0
   - Otherwise → continue

2. **Quality Reward**:
   - Compute model tour length `L_model`
   - Compute baseline tour length `L_baseline` (nearest neighbor from city 0)
   - Normalized reward: `r_quality = max(0.0, (L_baseline - L_model) / L_baseline)`
   - If model beats baseline, reward is positive
   - If model is worse, reward is 0

3. **Total Reward**:
   - `reward = validity * r_quality`
   - Range: [0.0, 1.0]

## Repository Structure

```
traveling-salesman-rl/
├── DEV_NOTES_TSP_ENV.md          # This file
├── README.md                      # Root README
├── environments/
│   └── tsp_rl_env/
│       ├── tsp_rl_env.py          # Main environment module
│       ├── pyproject.toml         # Package metadata
│       └── README.md              # Environment documentation
└── tests/
    └── test_tsp_rl_env.py         # Unit tests
```

## Implementation Checklist

- [x] Create planning document
- [ ] Examine repo structure
- [ ] Initialize environment with `prime env init tsp_rl_env`
- [ ] Implement synthetic dataset generation
- [ ] Implement TSP instance generation (coordinates, distance matrix)
- [ ] Implement nearest neighbor baseline heuristic
- [ ] Implement JSON parser for tour outputs
- [ ] Implement reward function
- [ ] Implement `load_environment` function
- [ ] Write environment README
- [ ] Create unit tests
- [ ] Test local installation (`uv pip install -e .`)
- [ ] Test with `vf-eval`
- [ ] Update root README
- [ ] Final verification

## Key Dependencies

- Python 3.11+
- `verifiers` (Verifiers framework)
- `datasets` (Hugging Face datasets)
- `numpy` (for numerical computations)
- `uv` (package manager)
- `prime` CLI (for publishing)

## Development Workflow

1. **Local Development**:
   ```bash
   cd environments/tsp_rl_env
   uv pip install -e .
   ```

2. **Local Testing**:
   ```bash
   uv run vf-eval tsp_rl_env -n 2 -r 1
   ```

3. **Publishing to Hub**:
   ```bash
   prime login
   cd environments/tsp_rl_env
   prime env push
   ```

## Technical Notes

### Instance Generation
- Use Python's `random.Random(seed)` for reproducibility
- Generate coordinates uniformly in [0, 1] × [0, 1]
- Precompute distance matrix to avoid recomputation
- Store coordinates and distance matrix in environment state

### Nearest Neighbor Baseline
- Start from city 0
- At each step, visit nearest unvisited city
- Return to city 0 at the end
- This provides a simple but reasonable baseline for normalization

### Parser Design
- Extract completion text
- Parse JSON with `json.loads`
- Validate `tour` field exists and is a list
- Validate tour is a valid permutation
- Return parsed tour or None on failure

### Verifiers Integration
- Use `vf.SingleTurnEnv` (or equivalent)
- Implement custom reward function with signature:
  ```python
  async def tsp_reward(completion, answer, state: vf.State, **kwargs) -> float
  ```
- Create `vf.Rubric` with reward function
- Return environment from `load_environment`

## Status

**COMPLETED** ✅ - Environment ready for publication to Prime Intellect's Environments Hub

### Completion Summary

All acceptance criteria have been met:

1. ✅ **Environment Module Created**: `environments/tsp_rl_env/` with complete implementation
   - `tsp_rl_env.py`: Full environment with synthetic dataset generation, TSP instance creation, reward function
   - `pyproject.toml`: Proper metadata, dependencies, and configuration
   - `README.md`: Comprehensive documentation

2. ✅ **Local Testing Successful**:
   - Environment loads correctly with `vf.load_environment('tsp_rl_env')`
   - All 32 unit tests pass
   - Can be installed with `uv pip install -e environments/tsp_rl_env`

3. ✅ **Environment Features**:
   - Synthetic TSP instances generated from random seeds
   - Single turn prompt-response format with strict JSON output
   - JSON parser validates tours are valid permutations
   - Reward function compares model tours to nearest neighbor baseline
   - Configurable instance sizes (10-30 cities by default)

4. ✅ **Documentation Complete**:
   - Root README with quick start and overview
   - Environment README with full task description, usage, and examples
   - Development notes documenting design decisions
   - Clear instructions for `prime env push` and `prime env eval`

5. ✅ **Code Quality**:
   - No syntax errors
   - Comprehensive test coverage
   - Clear docstrings on all functions
   - Well-organized module structure

### Next Steps for Users

1. **Authenticate with Prime**:
   ```bash
   prime login
   ```

2. **Publish Environment**:
   ```bash
   cd environments/tsp_rl_env
   prime env push
   ```

3. **Run Evaluations**:
   ```bash
   prime env eval <owner>/tsp-rl-env -m <model-name> -n 32 -r 3
   ```

### Technical Notes

- Environment uses `vf.SingleTurnEnv` with pre-computed dataset
- All TSP instance data (coordinates, distance matrix, baseline) stored in dataset rows
- Reward function accesses instance data from `state["info"]`
- Nearest neighbor baseline provides reasonable but beatable reference
- Reward range: [0.0, 1.0] with 0.0 for invalid/worse tours

---

Last Updated: 2025-11-18 (Final)
