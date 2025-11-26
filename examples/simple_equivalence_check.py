#!/usr/bin/env python3
"""
Simple example of using BEQ for equivalence checking.

This script demonstrates how to check if two Lean theorems are equivalent.
"""

import asyncio
import os
from pathlib import Path

# Ensure the parent directory is in the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.repl import REPL
from common.dataclasses import Environment


async def check_equivalence_example():
    """Example of checking if two theorems are equivalent."""

    # Example theorems
    thm_P = """
theorem thm_P : ¬ ∃ (x : ℚ), ( x ^ 2 = 12 ) :=
sorry
"""

    thm_Q = """
theorem thm_Q (q : ℚ ) :q ^ 2 ≠ 12 := by
sorry
"""

    # Configure paths (update these to match your setup)
    mathlib_root = Path(os.getenv("MATHLIB_ROOT", "/path/to/mathlib4"))
    repl_root = Path(os.getenv("REPL_ROOT", "/path/to/repl"))

    print("=" * 60)
    print("BEQ - Lean Equivalence Checker Example")
    print("=" * 60)
    print(f"\nTheorem P:\n{thm_P}")
    print(f"\nTheorem Q:\n{thm_Q}")
    print("\nChecking equivalence...")
    print("=" * 60)

    # Initialize REPL
    repl = REPL(
        repl_root=repl_root,
        project_root=mathlib_root,
        timeout=120
    )

    try:
        # Start REPL
        repl._run_interactive()

        # Load the theorems
        code = f"""
import Mathlib

open Topology Filter Real Complex TopologicalSpace Finset
open scoped BigOperators
noncomputable section

{thm_P}

{thm_Q}
"""

        result = repl.run_cmd(code)

        if isinstance(result, Environment):
            print("✓ Both theorems loaded successfully")
            print(f"  Environment ID: {result.env}")
            print(f"  Messages: {len(result.messages)}")

            # Check for errors
            errors = [m for m in result.messages if m.severity == 'error']
            if errors:
                print("\n✗ Errors found:")
                for err in errors:
                    print(f"  - {err.data}")
            else:
                print("\n✓ No type errors found")
                print("\nNote: To prove full equivalence, you would need to:")
                print("  1. Show thm_P → thm_Q")
                print("  2. Show thm_Q → thm_P")
                print("\nThis requires using LLM-based proof generation (see beq_basic.py)")
        else:
            print(f"✗ Error: {result}")

    except Exception as e:
        print(f"✗ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        repl._close()

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


def main():
    """Main entry point."""
    # Check if paths are configured
    mathlib_root = os.getenv("MATHLIB_ROOT")
    repl_root = os.getenv("REPL_ROOT")

    if not mathlib_root or not repl_root:
        print("⚠️  Warning: Environment variables not set!")
        print("\nPlease configure your environment:")
        print("  export MATHLIB_ROOT=/path/to/mathlib4")
        print("  export REPL_ROOT=/path/to/repl")
        print("\nOr create a .env file (see .env.example)")
        print("\nContinuing with default paths (this may fail)...\n")

    # Run the async example
    asyncio.run(check_equivalence_example())


if __name__ == "__main__":
    main()
