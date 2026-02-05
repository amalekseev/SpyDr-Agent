#!/usr/bin/env python3
import argparse
import os
import sys

# Add project root to sys.path to allow importing generator module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from manual_tests.generator.core import Generator
from manual_tests.generator.config import config

def main():
    parser = argparse.ArgumentParser(description="Generate human-readable manual tests from Gherkin feature files.")
    
    parser.add_argument(
        "--features-dir", 
        default="gherkin/features",
        help="Directory containing .feature files (default: gherkin/features)"
    )
    parser.add_argument(
        "--output-dir", 
        default="manual_tests/tests",
        help="Directory to save generated .txt files (default: manual_tests/tests)"
    )
    parser.add_argument(
        "--model", 
        help=f"OpenAI model to use (default: {config.MODEL_NAME})"
    )
    parser.add_argument(
        "--api-key", 
        help="OpenAI API Key (overrides env var)"
    )
    
    args = parser.parse_args()

    # Override config with CLI args if provided
    if args.model:
        config.MODEL_NAME = args.model
    
    if args.api_key:
        config.OPENAI_API_KEY = args.api_key
    
    # Check if API key is present (either from env or CLI)
    if not config.OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not set. Please set it as an environment variable or pass it via --api-key.")
        # We don't exit here because the Generator class handles missing key gracefully (skips generation), 
        # but it's good to warn loudly.
    
    # Resolve paths relative to current working directory
    features_dir = os.path.abspath(args.features_dir)
    output_dir = os.path.abspath(args.output_dir)

    print(f"Starting generation...")
    print(f"Features directory: {features_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Model: {config.MODEL_NAME}")
    
    generator = Generator(features_dir, output_dir)
    generator.run()
    
    print("Generation complete.")

if __name__ == "__main__":
    main()
