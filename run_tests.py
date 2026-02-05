#!/usr/bin/env python3
"""
Test Runner - Run all tests for enhanced bot
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py -v           # Verbose mode
    python run_tests.py --unit       # Only unit tests
    python run_tests.py --coverage   # With coverage report
"""

import sys
import subprocess
from pathlib import Path


def run_tests(args=None):
    """Run pytest with given arguments"""
    
    cmd = ["pytest"]
    
    if args is None:
        args = sys.argv[1:]
    
    # Parse custom arguments
    if "--unit" in args:
        cmd.extend(["-m", "unit"])
        args.remove("--unit")
    elif "--integration" in args:
        cmd.extend(["-m", "integration"])
        args.remove("--integration")
    
    if "--coverage" in args:
        cmd.extend(["--cov=bot", "--cov-report=html", "--cov-report=term"])
        args.remove("--coverage")
    
    # Add remaining arguments
    cmd.extend(args)
    
    # Add test directory
    test_dir = Path(__file__).parent / "tests"
    cmd.append(str(test_dir))
    
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
