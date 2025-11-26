# BEQ Examples

This directory contains example scripts demonstrating how to use BEQ.

## Examples

### 1. Simple Equivalence Check

**File**: `simple_equivalence_check.py`

Demonstrates basic usage of the REPL interface to check if two Lean theorems are well-typed.

**Usage**:
```bash
# Set environment variables
export MATHLIB_ROOT=/path/to/mathlib4
export REPL_ROOT=/path/to/repl

# Run the example
python examples/simple_equivalence_check.py
```

### 2. Full Equivalence Checking

For full equivalence checking using LLMs, see the main modules:

```bash
# Basic equivalence checking
python -m equivalence.beq_basic \
    --equiv_url http://localhost:13420/v1 \
    --equiv_model kimina_72b \
    --mathlib_root /path/to/mathlib4 \
    --repl_root /path/to/repl \
    --eval_set proofnet \
    --dataset_root ./data/ \
    --working_root ./results/
```

## Prerequisites

Before running these examples, ensure:

1. Lean 4 is installed with Mathlib4
2. Python dependencies are installed: `pip install -r requirements.txt`
3. Environment variables are configured (see `.env.example`)
4. An LLM server is running (for full equivalence checking)

## Understanding the Output

- ✓ indicates success
- ✗ indicates an error
- Environment ID: Unique identifier for the Lean environment
- Messages: Diagnostic messages from Lean (warnings, errors, etc.)

## Next Steps

After running these examples:

1. Explore the equivalence checking modules in `equivalence/`
2. Try different benchmarks in `data/`
3. Experiment with retrieval methods in `retriever/`
4. Implement auto-formalization using scripts in `autoformalizer/`

## Troubleshooting

**REPL timeout**: Increase timeout in `common/constants.py`

**Import errors**: Ensure BEQ is installed or the parent directory is in PYTHONPATH

**Lean errors**: Check that Mathlib4 is built with `lake build`
