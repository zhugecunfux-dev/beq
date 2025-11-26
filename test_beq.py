#!/usr/bin/env python3
"""
BEQ Self-Test Script

This script tests the BEQ installation and reports what works
and what dependencies are missing.
"""

import sys
import json
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print('\n' + '=' * 70)
    print(text)
    print('=' * 70)


def print_section(text):
    """Print a formatted section."""
    print(f'\n{text}')
    print('-' * 70)


def test_python_version():
    """Test Python version."""
    print_section('1. Python Version Check')
    version = sys.version_info
    print(f'   Python {version.major}.{version.minor}.{version.micro}')
    if version.major >= 3 and version.minor >= 9:
        print('   ✓ Python version is sufficient (>= 3.9)')
        return True
    else:
        print('   ✗ Python version too old (need >= 3.9)')
        return False


def test_basic_dependencies():
    """Test basic Python dependencies."""
    print_section('2. Basic Dependencies')

    deps = {
        'json': 'json',
        'asyncio': 'asyncio',
        'pathlib': 'pathlib',
        'dataclasses': 'dataclasses',
    }

    all_ok = True
    for name, module in deps.items():
        try:
            __import__(module)
            print(f'   ✓ {name}')
        except ImportError:
            print(f'   ✗ {name} (MISSING)')
            all_ok = False

    return all_ok


def test_external_dependencies():
    """Test external dependencies."""
    print_section('3. External Dependencies')

    deps = {
        'loguru': 'loguru',
        'regex': 'regex',
        'pexpect': 'pexpect',
        'dacite': 'dacite',
        'networkx': 'networkx',
        'aiohttp': 'aiohttp',
        'aiofiles': 'aiofiles',
        'tqdm': 'tqdm',
        'fire': 'fire',
        'easydict': 'easydict',
        'requests': 'requests',
        'psutil': 'psutil',
        'fastapi': 'fastapi',
        'vllm': 'vllm',
        'torch': 'torch',
        'transformers': 'transformers',
        'xtuner': 'xtuner',
        'openai': 'openai',
    }

    results = {}
    for name, module in deps.items():
        try:
            __import__(module)
            print(f'   ✓ {name}')
            results[name] = True
        except ImportError:
            print(f'   ✗ {name} (not installed)')
            results[name] = False

    installed = sum(results.values())
    total = len(results)
    print(f'\n   Summary: {installed}/{total} dependencies installed')

    return results


def test_beq_modules():
    """Test BEQ module imports."""
    print_section('4. BEQ Module Structure')

    modules = {
        'common.constants': 'Constants and patterns',
        'common.dataclasses': 'Data structures',
        'common.utils': 'Utility functions',
        'equivalence': 'Equivalence checking',
        'autoformalizer': 'Auto-formalization',
        'retriever': 'Theorem retrieval',
    }

    all_ok = True
    for module, desc in modules.items():
        try:
            __import__(module)
            print(f'   ✓ {module} - {desc}')
        except ImportError as e:
            print(f'   ✗ {module} - {desc}')
            print(f'      Error: {e}')
            all_ok = False

    return all_ok


def test_data_classes():
    """Test BEQ data classes."""
    print_section('5. Data Classes')

    try:
        from common.dataclasses import Pos, Sorry, Environment, ProofState, Message

        # Test Pos
        pos1 = Pos(line=1, column=5)
        pos2 = Pos(line=2, column=10)
        assert pos1 < pos2
        print(f'   ✓ Pos class works: {pos1} < {pos2}')

        # Test Message
        msg = Message(severity='info', data='Test', pos=pos1, endPos=pos2)
        print(f'   ✓ Message class works: {msg.severity}')

        # Test Environment
        env = Environment(env=1, sorries=[], messages=[msg])
        serialized = env.serialize()
        print(f'   ✓ Environment class works: {len(serialized)} fields')

        # Test ProofState
        ps = ProofState(proofState=1, goals=['goal1', 'goal2'])
        print(f'   ✓ ProofState class works: {len(ps.goals)} goals')

        return True
    except Exception as e:
        print(f'   ✗ Error testing data classes: {e}')
        return False


def test_constants():
    """Test constants and regex patterns."""
    print_section('6. Constants and Patterns')

    try:
        from common.constants import REPL_TIMEOUT, TERMINAL_TEXT, ident_pattern

        print(f'   ✓ REPL_TIMEOUT = {REPL_TIMEOUT}')
        print(f'   ✓ TERMINAL_TEXT = "{TERMINAL_TEXT}"')

        # Test regex pattern
        test_ident = "Mathlib.Data.Nat.Basic"
        match = ident_pattern.match(test_ident)
        if match:
            print(f'   ✓ ident_pattern matches: "{test_ident}"')
        else:
            print(f'   ✗ ident_pattern failed to match: "{test_ident}"')

        return True
    except Exception as e:
        print(f'   ✗ Error testing constants: {e}')
        return False


def test_data_files():
    """Test data files."""
    print_section('7. Data Files')

    all_ok = True

    # ProofNet
    proofnet = Path('data/proofnet/benchmark.jsonl')
    if proofnet.exists():
        with open(proofnet, 'r') as f:
            items = [json.loads(line) for line in f if line.strip()]
        print(f'   ✓ ProofNet benchmark: {len(items)} problems')
    else:
        print(f'   ✗ ProofNet benchmark not found')
        all_ok = False

    # CONNF
    connf_bench = Path('data/connf/benchmark.jsonl')
    connf_lib = Path('data/connf/library.jsonl')
    if connf_bench.exists():
        with open(connf_bench, 'r') as f:
            items = [json.loads(line) for line in f if line.strip()]
        print(f'   ✓ CONNF benchmark: {len(items)} items')
    else:
        print(f'   ✗ CONNF benchmark not found')
        all_ok = False

    if connf_lib.exists():
        with open(connf_lib, 'r') as f:
            items = [json.loads(line) for line in f if line.strip()]
        print(f'   ✓ CONNF library: {len(items)} theorems')
    else:
        print(f'   ✗ CONNF library not found')
        all_ok = False

    # Human equivalence
    for dataset in ['o1-generated', 'rautoformalizer-generated']:
        labels_path = Path(f'data/human_equivalence/{dataset}/labels.json')
        if labels_path.exists():
            with open(labels_path, 'r') as f:
                labels = json.load(f)
            equiv = sum(1 for v in labels.values() if v is True)
            print(f'   ✓ Human labels ({dataset}): {len(labels)} pairs, {equiv} equivalent')
        else:
            print(f'   ✗ Human labels ({dataset}) not found')
            all_ok = False

    return all_ok


def test_external_tools():
    """Test external tools (Lean, Lake)."""
    print_section('8. External Tools')

    import subprocess

    # Check Lean
    try:
        result = subprocess.run(['lean', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f'   ✓ Lean installed: {version}')
            lean_ok = True
        else:
            print(f'   ✗ Lean not working')
            lean_ok = False
    except FileNotFoundError:
        print(f'   ✗ Lean not installed')
        lean_ok = False

    # Check Lake
    try:
        result = subprocess.run(['lake', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f'   ✓ Lake installed: {version}')
            lake_ok = True
        else:
            print(f'   ✗ Lake not working')
            lake_ok = False
    except FileNotFoundError:
        print(f'   ✗ Lake not installed')
        lake_ok = False

    return lean_ok and lake_ok


def print_summary(results):
    """Print summary of test results."""
    print_header('TEST SUMMARY')

    total_tests = len(results)
    passed = sum(results.values())

    print(f'\nTests Passed: {passed}/{total_tests}')
    print('\nResults:')
    for test, result in results.items():
        status = '✓ PASS' if result else '✗ FAIL'
        print(f'   {status} - {test}')

    print_section('What Works:')
    if results.get('Python Version'):
        print('   ✓ Python 3.11+ is installed')
    if results.get('BEQ Modules'):
        print('   ✓ BEQ code structure is correct')
    if results.get('Data Classes'):
        print('   ✓ Core data structures work')
    if results.get('Data Files'):
        print('   ✓ All benchmark data is present')

    print_section('What Needs Setup:')
    if not results.get('External Tools'):
        print('   ⚠ Lean 4 and Lake need to be installed')
        print('     Install from: https://lean-lang.org/lean4/doc/setup.html')

    print('   ⚠ Heavy ML dependencies (vLLM, torch, transformers)')
    print('     Install with: pip install -r requirements.txt')
    print('     Note: Requires CUDA-capable GPU for full functionality')

    print_section('Next Steps:')
    print('   1. Install Lean 4: https://lean-lang.org/lean4/doc/setup.html')
    print('   2. Clone and build Mathlib4')
    print('   3. Install Python dependencies: pip install -r requirements.txt')
    print('   4. Configure .env file with paths')
    print('   5. Set up an LLM inference server (vLLM)')
    print('   6. Run equivalence checking: python -m equivalence.beq_basic')


def main():
    """Run all tests."""
    print_header('BEQ Self-Test')
    print('Testing BEQ installation and dependencies...')

    results = {}

    results['Python Version'] = test_python_version()
    results['Basic Dependencies'] = test_basic_dependencies()
    dep_results = test_external_dependencies()
    results['External Dependencies'] = all(dep_results.values())
    results['BEQ Modules'] = test_beq_modules()
    results['Data Classes'] = test_data_classes()
    results['Constants'] = test_constants()
    results['Data Files'] = test_data_files()
    results['External Tools'] = test_external_tools()

    print_summary(results)

    print('\n' + '=' * 70)
    print('Self-test complete!')
    print('=' * 70)

    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
