#!/usr/bin/env python3
"""
Database migration utility script

Usage:
  uv run migrate.py create "Add new column"  # Create new migration
  uv run migrate.py upgrade                  # Apply all pending migrations  
  uv run migrate.py downgrade <revision>     # Downgrade to specific revision
  uv run migrate.py current                  # Show current revision
  uv run migrate.py history                  # Show migration history
"""

import sys
import subprocess
import os
from pathlib import Path

def run_alembic(args):
    """Run alembic command with proper environment"""
    cmd = ["uv", "run", "alembic"] + args
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 3:
            print("Usage: uv run migrate.py create 'migration message'")
            sys.exit(1)
        message = sys.argv[2]
        print(f"Creating migration: {message}")
        run_alembic(["revision", "--autogenerate", "-m", message])
        
    elif command == "upgrade":
        print("Applying all pending migrations...")
        run_alembic(["upgrade", "head"])
        
    elif command == "downgrade":
        if len(sys.argv) < 3:
            print("Usage: uv run migrate.py downgrade <revision>")
            sys.exit(1)
        revision = sys.argv[2]
        print(f"Downgrading to revision: {revision}")
        run_alembic(["downgrade", revision])
        
    elif command == "current":
        print("Current database revision:")
        run_alembic(["current"])
        
    elif command == "history":
        print("Migration history:")
        run_alembic(["history", "--verbose"])
        
    elif command == "stamp":
        if len(sys.argv) < 3:
            print("Usage: uv run migrate.py stamp <revision>")
            sys.exit(1)
        revision = sys.argv[2]
        print(f"Stamping database with revision: {revision}")
        run_alembic(["stamp", revision])
        
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
