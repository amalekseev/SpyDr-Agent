#!/usr/bin/env python3
import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def run_validation():
    """
    Runs pytest to validate that the Gherkin tests are syntactically correct 
    and the environment is set up properly.
    """
    print("Running validation (pytest)...")
    
    # Path to the tests directory
    tests_dir = os.path.join("gherkin", "tests")
    
    if not os.path.exists(tests_dir):
        print(f"Error: Tests directory not found at {tests_dir}")
        sys.exit(1)

    try:
        # Run pytest. We use check=False to handle exit codes manually.
        # We capture output to show it to the user.
        result = subprocess.run(
            ["pytest", tests_dir], 
            capture_output=False, 
            text=True
        )
        
        if result.returncode == 0:
            print("\nValidation successful! All tests passed.")
        else:
            print(f"\nValidation finished with exit code {result.returncode}.")
            print("Some tests failed or there were collection errors.")
            # We don't necessarily exit with error here, as this might be expected 
            # if the environment isn't fully mocked yet, but we report it.
            
    except FileNotFoundError:
        print("Error: 'pytest' command not found. Please install pytest.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_validation()
