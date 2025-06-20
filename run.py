#!/usr/bin/env python3
"""
CLI entry point for the AI red-teaming tool.
"""
import sys
import asyncio
from pathlib import Path

# Add src to path so we can import modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.main import main

if __name__ == "__main__":
    asyncio.run(main())
