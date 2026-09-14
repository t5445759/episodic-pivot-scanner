#!/usr/bin/env python
"""Entry point for running the orchestrator in continuous mode."""
import asyncio
from src.orchestrator.orchestrator import run_orchestrator

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 Episodic Pivot Scanner - Continuous Mode")
    print("="*80 + "\n")
    
    # Run orchestrator
    asyncio.run(run_orchestrator(mode='continuous'))
