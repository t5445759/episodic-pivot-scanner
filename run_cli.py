#!/usr/bin/env python
"""Entry point for running the CLI."""
import asyncio
import sys
from src.cli.cli import cli

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 Episodic Pivot Scanner CLI")
    print("="*80 + "\n")
    
    try:
        cli()
    except KeyboardInterrupt:
        print("\n\n⏹️  Scanner stopped by user")
        sys.exit(0)
