#!/usr/bin/env python3
"""
Test the Lean REPL standalone to diagnose crashes.
"""

import sys
import asyncio
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from common.repl import REPL
from common.dataclasses import Environment

async def test_repl():
    """Test REPL with progressively complex inputs."""

    mathlib_root = Path("/mnt/disk0/t00917290/imo_autoformalization/rethinking_autoformalization/mathlib4")
    repl_root = Path("/mnt/disk0/t00917290/imo_autoformalization/rethinking_autoformalization/repl")

    print("="*70)
    print("REPL Standalone Test")
    print("="*70)

    print(f"\n📍 Paths:")
    print(f"   Mathlib: {mathlib_root}")
    print(f"   REPL: {repl_root}")
    print(f"   REPL binary: {repl_root}/.lake/build/bin/repl")

    # Check if paths exist
    if not mathlib_root.exists():
        print(f"\n❌ ERROR: Mathlib root doesn't exist!")
        return False
    if not (repl_root / ".lake/build/bin/repl").exists():
        print(f"\n❌ ERROR: REPL binary doesn't exist!")
        print(f"   Build it with: cd {repl_root} && lake build")
        return False

    print("\n✓ Paths exist")

    # Test 1: Start REPL
    print("\n" + "="*70)
    print("Test 1: Starting REPL...")
    print("="*70)

    repl = REPL(repl_root=repl_root, project_root=mathlib_root, timeout=120)

    try:
        repl._run_interactive()
        print("✓ REPL started successfully")
    except Exception as e:
        print(f"❌ REPL failed to start: {e}")
        return False

    await asyncio.sleep(2)  # Give it time to initialize

    # Test 2: Simple command
    print("\n" + "="*70)
    print("Test 2: Simple import...")
    print("="*70)

    try:
        result = await repl.run_cmd_async("import Mathlib")
        if isinstance(result, Environment):
            print(f"✓ Import successful (env={result.env})")
            print(f"  Messages: {len(result.messages)}")
            for msg in result.messages[:3]:
                print(f"    - {msg.severity}: {msg.data[:60]}")
        else:
            print(f"❌ Import failed: {result}")
            repl._close()
            return False
    except Exception as e:
        print(f"❌ Import crashed: {type(e).__name__}: {e}")
        repl._close()
        return False

    # Test 3: Header from CONNF problem
    print("\n" + "="*70)
    print("Test 3: CONNF-style header...")
    print("="*70)

    header = """import Mathlib

open Real
open scoped BigOperators
noncomputable section
"""

    try:
        result = await repl.run_cmd_async(header)
        if isinstance(result, Environment):
            print(f"✓ Header successful (env={result.env})")
            errors = [m for m in result.messages if m.severity == 'error']
            if errors:
                print(f"  ⚠️  {len(errors)} errors:")
                for err in errors[:3]:
                    print(f"    - {err.data[:80]}")
            else:
                print(f"  No errors")
        else:
            print(f"❌ Header failed: {result}")
    except Exception as e:
        print(f"❌ Header crashed: {type(e).__name__}: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        repl._close()
        return False

    # Test 4: Theorem statement
    print("\n" + "="*70)
    print("Test 4: Simple theorem...")
    print("="*70)

    theorem = """theorem test_thm : 1 + 1 = 2 := by sorry"""

    try:
        result = await repl.run_cmd_async(theorem)
        if isinstance(result, Environment):
            print(f"✓ Theorem successful (env={result.env})")
            print(f"  Sorries: {len(result.sorries)}")
        else:
            print(f"❌ Theorem failed: {result}")
    except Exception as e:
        print(f"❌ Theorem crashed: {type(e).__name__}: {e}")
        repl._close()
        return False

    # Cleanup
    repl._close()
    print("\n" + "="*70)
    print("✅ All tests passed!")
    print("="*70)
    print("\nREPL is working correctly. The crash might be:")
    print("  1. Specific to certain problems in your dataset")
    print("  2. Due to memory pressure when running many in parallel")
    print("  3. Caused by malformed Lean code in some problems")
    print("\nRecommendation:")
    print("  - Run with --num_concurrency 1 (you already are)")
    print("  - Add --try_num 1 to reduce load")
    print("  - Check which specific problem causes the crash")

    return True

if __name__ == "__main__":
    success = asyncio.run(test_repl())
    sys.exit(0 if success else 1)
