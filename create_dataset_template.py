#!/usr/bin/env python3
"""
Create a minimal BEQ dataset template.

Usage:
    python create_dataset_template.py my_dataset_name
"""

import sys
import json
from pathlib import Path

def create_template(dataset_name):
    """Create a minimal BEQ dataset template."""

    # Create directories
    dataset_dir = Path(f"data/{dataset_name}")
    dataset_dir.mkdir(parents=True, exist_ok=True)

    working_dir = Path(f"results_{dataset_name}")
    working_dir.mkdir(parents=True, exist_ok=True)

    # Create benchmark.jsonl
    benchmark = [
        {
            "full_name": f"{dataset_name}.example_1",
            "formal_stmt": "theorem example_1 (n : ℕ) : n + 0 = n := by sorry",
            "header": "import Mathlib\n\nopen Nat\nnoncomputable section\n\n",
            "informal_stmt": "Adding zero to any natural number gives the same number",
            "proof_state": "⊢ n + 0 = n",
            "mathlib_dependencies": ["Mathlib.Data.Nat.Basic"],
            "hard_dependencies": [],
            "source": dataset_name,
            "problem_name": "example_1"
        },
        {
            "full_name": f"{dataset_name}.example_2",
            "formal_stmt": "theorem example_2 (a b : ℕ) : a + b = b + a := by sorry",
            "header": "import Mathlib\n\nopen Nat\nnoncomputable section\n\n",
            "informal_stmt": "Addition of natural numbers is commutative",
            "proof_state": "⊢ a + b = b + a",
            "mathlib_dependencies": ["Mathlib.Data.Nat.Basic"],
            "hard_dependencies": [],
            "source": dataset_name,
            "problem_name": "example_2"
        }
    ]

    benchmark_file = dataset_dir / "benchmark.jsonl"
    with open(benchmark_file, 'w') as f:
        for item in benchmark:
            f.write(json.dumps(item) + '\n')

    print(f"✓ Created {benchmark_file}")

    # Create autoformalization.json
    autoformalization = {
        f"{dataset_name}.example_1": [{
            "autoformalized_statement": "theorem thm_Q (n : ℕ) : n + 0 = n := by sorry",
            "typecheck_result": {
                "is_success": True,
                "lean_env": 1
            },
            "metadata": {
                "note": "This is a placeholder - replace with your actual Lean code"
            }
        }],
        f"{dataset_name}.example_2": [{
            "autoformalized_statement": "theorem thm_Q (a b : ℕ) : a + b = b + a := by sorry",
            "typecheck_result": {
                "is_success": True,
                "lean_env": 1
            },
            "metadata": {
                "note": "This is a placeholder - replace with your actual Lean code"
            }
        }]
    }

    autoform_file = working_dir / "autoformalization.json"
    with open(autoform_file, 'w') as f:
        json.dump(autoformalization, f, indent=2)

    print(f"✓ Created {autoform_file}")

    # Create README
    readme = f"""# {dataset_name} Dataset for BEQ

## Files Created

- `data/{dataset_name}/benchmark.jsonl` - Problem definitions
- `results_{dataset_name}/autoformalization.json` - Autoformalization results

## How to Use

1. **Edit the benchmark:**
   ```bash
   nano data/{dataset_name}/benchmark.jsonl
   ```
   Add your problems (one JSON per line).

2. **Edit autoformalization results:**
   ```bash
   nano results_{dataset_name}/autoformalization.json
   ```
   Add your Lean code for each problem.

3. **Run BEQ:**
   ```bash
   python -m equivalence.beq_basic \\
       --equiv_url http://localhost:13423/v1 \\
       --equiv_model your_model \\
       --eval_set {dataset_name} \\
       --dataset_root ./data \\
       --working_root ./results_{dataset_name} \\
       --mathlib_root /path/to/mathlib4 \\
       --repl_root /path/to/repl \\
       --num_concurrency 1
   ```

## Required Fields

### benchmark.jsonl (each line):
- `full_name`: Unique problem identifier
- `formal_stmt`: Ground truth Lean theorem
- `header`: Lean imports and setup
- `source`: Dataset name
- `problem_name`: Short problem name

### autoformalization.json:
- Key: Problem `full_name`
- Value: List of attempts, each with:
  - `autoformalized_statement`: Generated Lean code
  - `typecheck_result`: Success status

## Next Steps

1. Replace the example problems with your own
2. Generate or write Lean code for each problem
3. Run BEQ to check equivalence
"""

    readme_file = dataset_dir / "README.md"
    with open(readme_file, 'w') as f:
        f.write(readme)

    print(f"✓ Created {readme_file}")

    print("\n" + "="*70)
    print(f"✅ Template dataset '{dataset_name}' created!")
    print("="*70)
    print(f"\n📁 Files created:")
    print(f"   - data/{dataset_name}/benchmark.jsonl (2 example problems)")
    print(f"   - results_{dataset_name}/autoformalization.json (2 examples)")
    print(f"   - data/{dataset_name}/README.md (usage guide)")

    print(f"\n📝 Next steps:")
    print(f"   1. Edit data/{dataset_name}/benchmark.jsonl - add your problems")
    print(f"   2. Edit results_{dataset_name}/autoformalization.json - add Lean code")
    print(f"   3. Run BEQ with --eval_set {dataset_name}")

    print(f"\n💡 Tip: Check the README for detailed instructions!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_dataset_template.py <dataset_name>")
        print("\nExample:")
        print("  python create_dataset_template.py my_math_problems")
        sys.exit(1)

    dataset_name = sys.argv[1]
    create_template(dataset_name)
