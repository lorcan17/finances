#!/usr/bin/env python3
"""
Setup script to create necessary directories and initialize the environment.
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Create necessary directories and verify environment."""
    print("Setting up transaction categorizer environment...")
    
    # Get base directory
    base_dir = Path(__file__).resolve().parent
    
    # Create directories
    dirs_to_create = [
        base_dir / "logs",
        base_dir / "config",
        base_dir / "utils",
        base_dir / "tests",
    ]
    
    for directory in dirs_to_create:
        if not directory.exists():
            print(f"Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py for Python packages
            if directory.name in ["config", "utils", "tests"]:
                init_file = directory / "__init__.py"
                if not init_file.exists():
                    print(f"Creating {init_file}")
                    init_file.touch()
    
    # Check for .env file
    env_file = base_dir / ".env"
    if not env_file.exists():
        print("\nWARNING: No .env file found.")
        print("Please create a .env file with your OpenAI API key:")
        print("Example:")
        print("OPENAI_API_KEY=your-api-key-here")
    
    # Check for Google credentials
    google_creds = base_dir / "config" / "encrypt_google_cloud_credentials.json"
    if not google_creds.exists():
        print("\nWARNING: Google credentials file not found.")
        print(f"Please place your Google Cloud credentials at: {google_creds}")
    
    print("\nSetup complete!")
    print("You can now run the transaction categorizer with:")
    print("python transaction_categorizer.py")

if __name__ == "__main__":
    setup_environment()