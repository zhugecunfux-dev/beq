# BEQ Testing Guide

This document provides information about testing the BEQ system.

## Quick Self-Test

Run the comprehensive self-test to check your installation:

```bash
python3 test_beq.py
```

This will check:
- ✓ Python version (need 3.9+)
- ✓ Core dependencies
- ⚠️ External dependencies (vLLM, torch, etc.)
- ✓ BEQ module structure
- ✓ Data classes and utilities
- ✓ Benchmark data files
- ⚠️ External tools (Lean 4, Lake)

## What the Tests Cover

### 1. Core Functionality (No External Dependencies)

These components work without Lean or heavy ML libraries:

**Data Structures:**
- ✓ `Pos` - Position tracking in code
- ✓ `Message` - Lean diagnostic messages
- ✓ `Environment` - Lean environment state
- ✓ `ProofState` - Proof state representation
- ✓ `Sorry` - Incomplete proof markers

**Utilities:**
- ✓ Regex patterns for Lean identifiers
- ✓ Constants (timeouts, patterns)
- ✓ Data serialization/deserialization

**Data:**
- ✓ ProofNet benchmark (10 problems)
- ✓ CONNF benchmark (374 problems, 1348 library theorems)
- ✓ Human equivalence labels (200 labeled pairs)

### 2. Components Requiring Dependencies

These require external setup:

**Lean Integration:**
- ⚠️ REPL interface (needs Lean 4 + Lake)
- ⚠️ Theorem verification (needs Mathlib4)

**LLM Features:**
- ⚠️ Equivalence checking (needs vLLM server)
- ⚠️ Auto-formalization (needs LLM models)
- ⚠️ Retrieval (needs transformers)

## Test Results from Self-Test

### ✓ What Currently Works

```
Tests Passed: 5/8

✓ Python Version (3.11.14)
✓ Basic Dependencies (json, asyncio, pathlib, dataclasses)
✓ Data Classes (Pos, Message, Environment, ProofState)
✓ Constants and Regex Patterns
✓ Data Files (all benchmarks present and valid)
```

### ⚠️ What Needs Installation

**Missing Python Dependencies:**
- aiohttp, aiofiles (async I/O)
- tqdm (progress bars)
- fire, easydict (CLI utilities)
- psutil (system monitoring)
- fastapi (web server)
- vllm, torch, transformers (ML)
- xtuner (training utilities)
- openai (API client)

**Missing External Tools:**
- Lean 4 (theorem prover)
- Lake (Lean build tool)
- Mathlib4 (Lean mathematics library)

## Installation Steps

### 1. Basic Installation (Testing Data & Structure)

```bash
pip install loguru regex pexpect dacite networkx requests
```

This allows you to:
- Test data structures
- Validate data files
- Explore benchmarks
- Run the self-test

### 2. Full Installation (All Features)

```bash
# Install all Python dependencies
pip install -r requirements.txt

# Install Lean 4 (follow official guide)
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh

# Clone and build Mathlib4
git clone https://github.com/leanprover-community/mathlib4
cd mathlib4
lake build
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your paths:
# - MATHLIB_ROOT=/path/to/mathlib4
# - REPL_ROOT=/path/to/repl
```

## Running Tests

### Self-Test Script

```bash
python3 test_beq.py
```

Output shows:
- ✓ What works
- ✗ What's missing
- ⚠️ What needs setup
- 📝 Next steps

### Manual Testing

**Test data structures:**
```python
from common.dataclasses import Pos, Environment, ProofState

pos = Pos(line=1, column=5)
print(pos)  # (1, 5)
```

**Test data loading:**
```python
import json

with open('data/proofnet/benchmark.jsonl', 'r') as f:
    problem = json.loads(f.readline())
    print(problem['id'])  # c463
```

**Test regex patterns:**
```python
from common.constants import ident_pattern

match = ident_pattern.match("Mathlib.Data.Nat.Basic")
print(match is not None)  # True
```

## Expected Behavior

### Without Lean Installed

```
✓ Core data structures work
✓ Data files can be loaded and analyzed
✓ Module structure is valid
✗ REPL tests fail (expected - needs Lean)
✗ Equivalence checking unavailable
```

### With Lean + Dependencies

```
✓ All core features
✓ REPL communication
✓ Theorem verification
✓ Full equivalence checking (with LLM server)
```

## Troubleshooting

**ImportError: No module named 'X'**
- Solution: `pip install X` or `pip install -r requirements.txt`

**Lean not found**
- Solution: Install from https://lean-lang.org/lean4/doc/setup.html

**REPL timeout**
- Solution: Increase `REPL_TIMEOUT` in `common/constants.py`

**GPU out of memory**
- Solution: Use smaller models or reduce batch size

## Test Data Overview

### ProofNet Benchmark (10 problems)

- All problems successfully formalized
- Includes informal statements and Lean code
- Has verification results
- Categories: math problems (domain, continuity, etc.)

### CONNF Benchmark (374 problems + 1348 library theorems)

- Formal/informal statement pairs
- Mathlib dependencies tracked
- Proof states included
- Source attribution

### Human Equivalence Labels (200 pairs)

**o1-generated:**
- 100 labeled pairs
- 39% equivalent, 61% not equivalent

**rautoformalizer-generated:**
- 100 labeled pairs
- 31% equivalent, 69% not equivalent

## Contributing Tests

When adding features, please:
1. Update `test_beq.py` with new tests
2. Document expected behavior
3. Mark tests requiring external dependencies
4. Add sample data if needed

## CI/CD (Future)

Future plans:
- GitHub Actions workflow
- Automated testing on commits
- Coverage reporting
- Performance benchmarks
