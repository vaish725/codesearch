#!/usr/bin/env python3
"""
Basic usage example for codesearch.

This example demonstrates:
1. Indexing a repository
2. Running text searches
3. Using symbol filters
4. Handling results
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from codesearch.storage.db import Database
from codesearch.config import get_db_path


def main():
    """Run basic codesearch examples."""
    
    print("🔍 Codesearch Basic Usage Example\n")
    
    # Example 1: Initialize database
    print("1. Initializing database...")
    db_path = get_db_path()
    db = Database(db_path)
    db.connect()
    db.initialize_schema()
    print(f"   ✓ Database created at: {db_path}\n")
    
    # Example 2: Index a repository (Phase 1)
    print("2. Indexing a repository...")
    print("   (Implementation coming in Phase 1)\n")
    
    # Example 3: Search for code (Phase 1)
    print("3. Searching for code...")
    print("   Example queries:")
    print("   - 'authentication'")
    print("   - 'def:process_payment'")
    print("   - 'class:User lang:python'")
    print("   (Implementation coming in Phase 1)\n")
    
    # Example 4: Symbol search (Phase 3)
    print("4. Symbol-aware search...")
    print("   Example: Find all definitions of 'User' class")
    print("   (Implementation coming in Phase 3)\n")
    
    print("✅ Example complete!")
    print("\nFor more examples, see the documentation at docs/")
    
    db.close()


if __name__ == "__main__":
    main()
