# BEQ - Lean Equivalence Checker

BEQ (Balanced Equivalence Quotient) is a sophisticated equivalence checker for Lean 4 theorem statements. It combines formal verification with large language models to verify whether different mathematical statements are formally equivalent.

## Overview

This project validates whether different formal/informal representations of mathematical theorems are logically equivalent, with applications to:
- Automated theorem proving
- Mathematical formalization
- Auto-formalization from natural language to Lean 4

## Key Features

- **Multiple Equivalence Strategies**: Basic, Normal, Advanced, and All-inclusive checking modes
- **LLM Integration**: Support for Deepseek and Qwen models via vLLM
- **Retrieval Augmentation**: BM25 and dense retrieval for theorem lookup
- **Lean 4 Integration**: Direct REPL interaction with Lean 4 type checker
- **Async Architecture**: High-performance concurrent proof verification

## Project Structure

```
beq/
├── equivalence/          # Core equivalence checking logic
│   ├── beq_basic.py     # Basic equivalence checker
│   ├── beq_normal.py    # Standard equivalence checker
│   ├── beq_advanced.py  # Advanced equivalence checker
│   ├── beq_all.py       # Comprehensive checker
│   ├── llm_grader_deepseek.py  # Deepseek model grader
│   ├── llm_grader_qwen.py      # Qwen model grader
│   ├── def_eq.py        # Definitional equality checker
│   └── id_match.py      # Identity matching
├── autoformalizer/      # Auto-formalization scripts
│   ├── autoformalize_vllm_passk.py
│   ├── autoformalize_vllm_w_gt_passk.py
│   └── autoformalize_vllm_w_ra_passk.py
├── retriever/           # Retrieval modules
│   ├── retrieve_bm25.py # BM25 keyword retrieval
│   └── retrieve_dr.py   # Dense retrieval
├── common/              # Shared utilities
│   ├── repl.py          # Lean 4 REPL interface
│   ├── dataclasses.py   # Type definitions
│   ├── constants.py     # Regex patterns
│   └── utils.py         # Helper functions
├── data/                # Datasets and benchmarks
│   ├── proofnet/        # ProofNet benchmark
│   ├── connf/           # CONNF benchmark
│   └── human_equivalence/ # Human-labeled data
└── monitor_run.sh       # Resource monitoring script
```

## Installation

### Prerequisites

- Python 3.9+
- Lean 4 with Mathlib4
- CUDA-capable GPU (for vLLM)
- `lake` (Lean package manager)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd beq
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Lean 4 and Mathlib4:
```bash
# Install Lean 4 (follow official instructions)
# Clone and build Mathlib4
git clone https://github.com/leanprover-community/mathlib4
cd mathlib4
lake build
```

4. Configure environment variables (copy and edit `.env.example`):
```bash
cp .env.example .env
# Edit .env with your paths and settings
```

## Usage

### Basic Equivalence Checking

```bash
export BEQ_LEVEL=basic
export EQ_BENCHMARK=o1-generated

python -m equivalence.beq_${BEQ_LEVEL} \
    --equiv_url http://localhost:13420/v1 \
    --equiv_model kimina_72b \
    --mathlib_root /path/to/mathlib4 \
    --eval_set proofnet \
    --working_root ./results \
    --dataset_root ./data/ \
    --repl_root /path/to/repl \
    --try_num 16 \
    --num_concurrency 1 \
    --temperature 0.0
```

### Equivalence Levels

- **basic**: Fast, simple equivalence checking
- **normal**: Standard equivalence checking with moderate complexity
- **advanced**: Sophisticated checking with multiple strategies
- **all**: Comprehensive checking using all available methods

### Using the Monitor Script

The `monitor_run.sh` script provides resource monitoring:

```bash
./monitor_run.sh
```

This will:
- Monitor memory and GPU usage
- Run equivalence checking
- Save logs to `memory_log.txt`

## Configuration

### Environment Variables

- `BEQ_LEVEL`: Equivalence checking level (basic/normal/advanced/all)
- `EQ_BENCHMARK`: Benchmark dataset to use
- `equiv_model`: LLM model name
- `mathlib_root`: Path to Mathlib4
- `repl_root`: Path to Lean REPL
- `dataset_root`: Path to datasets
- `working_root`: Output directory

## Data Format

### Benchmark Data (JSONL)

```json
{
  "id": "c463",
  "informal": "Compute the domain of...",
  "category": "unknown",
  "lean_code": "import Mathlib\ntheorem question126_560: ...",
  "response": "<think>...</think>\nlean code...",
  "success": true,
  "Check": 1
}
```

### Human Equivalence Labels (JSON)

```json
{
  "theorem statement 1": true,
  "theorem statement 2": false
}
```

## Architecture

### Data Flow

1. **Input**: Informal mathematical statements + formal Lean code
2. **Auto-formalization**: Convert natural language to Lean (optional)
3. **Retrieval**: Find relevant theorems using BM25/dense retrieval
4. **LLM Grading**: Evaluate equivalence using language models
5. **Verification**: REPL interaction with Lean 4 type checker
6. **Output**: Equivalence labels and verification results

### Key Components

- **REPL Interface**: Async communication with Lean 4
- **vLLM Engine**: High-performance LLM inference
- **Equivalence Strategies**: Multiple approaches for robust checking
- **Retrieval System**: Efficient theorem lookup

## Benchmarks

### Available Datasets

- **ProofNet**: General proof problems (10 examples)
- **CONNF**: Specialized benchmark (374 examples, 1348 library theorems)
- **Human Equivalence**: Human-labeled equivalence pairs
  - `o1-generated`: 101 labeled pairs
  - `rautoformalizer-generated`: 101 labeled pairs

## Development

### Running Tests

```bash
# TODO: Add test suite
pytest tests/
```

### Code Style

This project follows standard Python conventions. Use:
```bash
black .
isort .
flake8 .
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Citation

If you use this code in your research, please cite:

```bibtex
@software{beq2024,
  title={BEQ: Lean Equivalence Checker},
  author={},
  year={2024},
  url={https://github.com/...}
}
```

## License

[Add appropriate license]

## Acknowledgments

- Built on [Lean 4](https://lean-lang.org/) and [Mathlib4](https://github.com/leanprover-community/mathlib4)
- Uses [vLLM](https://github.com/vllm-project/vllm) for efficient LLM inference
- Integrates with Deepseek and Qwen language models

## Troubleshooting

### Common Issues

1. **REPL Timeout**: Increase `REPL_TIMEOUT` in `common/constants.py`
2. **GPU Memory**: Adjust batch size or use smaller models
3. **Lean Build Errors**: Ensure Mathlib4 is properly built with `lake build`

### Getting Help

- Open an issue on GitHub
- Check existing issues for similar problems
- Consult Lean 4 documentation

## Roadmap

- [ ] Add comprehensive test suite
- [ ] Support for additional LLM backends
- [ ] Web interface for equivalence checking
- [ ] Integration with proof assistant IDEs
- [ ] Improved retrieval strategies
- [ ] Multi-language support beyond Lean 4
