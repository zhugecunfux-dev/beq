#!/usr/bin/env python3
"""
Convert o1-generated autoformalization.jsonl to BEQ-compatible autoformalization.json

The o1-generated file is in JSONL format (ProofNet style).
BEQ expects a JSON dictionary mapping problem names to autoformalization attempts.
"""

import json
from pathlib import Path

print("Converting o1-generated/autoformalization.jsonl to BEQ format...")
print("=" * 70)

# Read JSONL file
input_file = Path('data/human_equivalence/o1-generated/autoformalization.jsonl')
with open(input_file, 'r') as f:
    problems = [json.loads(line) for line in f if line.strip()]

print(f"Loaded {len(problems)} problems from {input_file}")

# Convert to BEQ format
# Format: {problem_id: [list of autoformalization attempts]}
autoformalization_result = {}

for prob in problems:
    problem_id = prob['id']  # Use 'id' as the key
    lean_code = prob.get('lean_code', '')

    # Extract just the theorem part (remove imports and solution defs)
    # BEQ expects the theorem statement
    theorem_lines = [line for line in lean_code.split('\n') if 'theorem' in line]
    if theorem_lines:
        # Get everything from 'theorem' onwards
        theorem_start = lean_code.find('theorem')
        theorem_code = lean_code[theorem_start:] if theorem_start >= 0 else lean_code
    else:
        theorem_code = lean_code

    # Check if verification was successful
    verification = prob.get('verification_result', {})
    is_valid = verification.get('is_valid', False) if verification else False

    # Create autoformalization attempt in BEQ format
    attempt = {
        "autoformalized_statement": theorem_code.strip(),
        "typecheck_result": {
            "is_success": is_valid,
            "lean_env": 1,  # Dummy env ID
            "verification_details": verification
        },
        # Include metadata for reference
        "metadata": {
            "original_id": prob['id'],
            "informal": prob.get('informal', ''),
            "success": prob.get('success', False),
            "Check": prob.get('Check', -1),
            "status": prob.get('status', 'unknown')
        }
    }

    # BEQ expects a list of attempts (can have multiple)
    autoformalization_result[problem_id] = [attempt]

    print(f"  ✓ {problem_id}: {len(theorem_code)} chars, valid={is_valid}")

# Save to BEQ-compatible JSON format
output_file = Path('data/human_equivalence/o1-generated/autoformalization.json')
with open(output_file, 'w') as f:
    json.dump(autoformalization_result, f, indent=2)

print("\n" + "=" * 70)
print(f"✅ Conversion complete!")
print(f"   Input:  {input_file} (JSONL)")
print(f"   Output: {output_file} (JSON)")
print(f"   Problems: {len(autoformalization_result)}")

# Show sample structure
sample_key = list(autoformalization_result.keys())[0]
print(f"\n📋 Sample structure:")
print(f"   Problem: {sample_key}")
print(f"   Attempts: {len(autoformalization_result[sample_key])}")
print(f"   Fields: {list(autoformalization_result[sample_key][0].keys())}")

print("\n✨ Now you can use this with BEQ!")
print(f"\n   However, note that o1-generated uses 'id' field,")
print(f"   while CONNF uses 'full_name'. Make sure your benchmark")
print(f"   dataset matches this format.")
