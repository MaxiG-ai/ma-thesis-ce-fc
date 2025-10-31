import sys
from pathlib import Path
from BenchmarkAdapter import BenchmarkAdapter

#!/usr/bin/env python3
"""
Entry point script for MCP Benchmark Runner.

This script provides a convenient way to run the benchmark system
without needing to use module syntax.
"""

# Add project root to Python path (one level above this script)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import asyncio

    # Import and run the main function from benchmark runner
    try:
        from benchmark.runner import main

        asyncio.run(main())
    except ImportError as e:
        print(f"Import error: {e}")
        print(
            "Please ensure all dependencies are installed and you're running from the project root."
        )
        sys.exit(1)