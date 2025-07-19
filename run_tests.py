#!/usr/bin/env python3
"""
Test runner script for the AI Agent project
"""
import os
import sys
import subprocess
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run tests with specified options"""
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Base pytest command
    cmd = ["/Users/raees/.pyenv/versions/3.10.18/bin/python", "-m", "pytest"]
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env['PYTHONPATH'] = 'src'
    
    # Choose test files based on type
    if test_type == "all":
        cmd.append("tests/test_all.py")
    elif test_type == "models":
        cmd.append("tests/test_models.py")
    else:
        cmd.append("tests/")
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
    else:
        cmd.append("--no-cov")
    
    # Add output formatting
    cmd.extend(["--tb=short", "--disable-warnings"])
    
    print(f"🧪 Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, env=env, check=True)
        print("-" * 60)
        print("✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("-" * 60)
        print(f"❌ Tests failed with exit code {e.returncode}")
        return False


def run_specific_test(test_file, test_function=None):
    """Run a specific test file or function"""
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    cmd = ["/Users/raees/.pyenv/versions/3.10.18/bin/python", "-m", "pytest", "-v"]
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env['PYTHONPATH'] = 'src'
    
    if test_function:
        cmd.append(f"tests/{test_file}::{test_function}")
    else:
        cmd.append(f"tests/{test_file}")
    
    print(f"🎯 Running specific test: {test_file}::{test_function or 'all'}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, env=env, check=True)
        print("-" * 60)
        print("✅ Test passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("-" * 60)
        print(f"❌ Test failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests for AI Agent project")
    parser.add_argument("--type", choices=["all", "models"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--coverage", action="store_true", 
                       help="Enable coverage reporting")
    parser.add_argument("--file", help="Run specific test file")
    parser.add_argument("--function", help="Run specific test function (requires --file)")
    
    args = parser.parse_args()
    
    if args.file:
        success = run_specific_test(args.file, args.function)
    else:
        success = run_tests(
            test_type=args.type,
            verbose=args.verbose,
            coverage=args.coverage
        )
    
    if success:
        print("\n🎉 Testing complete!")
        print("\nAvailable test types:")
        print("  --type all     : Run all tests (recommended)")
        print("  --type models  : Run model validation tests only")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
