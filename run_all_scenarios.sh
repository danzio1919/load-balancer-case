#!/usr/bin/env bash
set -e

# Run all scenarios in the scenarios/ folder
for scenario_dir in scenarios/*/; do
  if [ -d "$scenario_dir" ]; then
    scenario=$(basename "$scenario_dir")
    echo "========================================"
    echo "Running simulation for: $scenario"
    echo "========================================"
    python3 run_simulation.py "$scenario"
    echo ""
  fi
done

echo "All scenarios validated successfully!"
