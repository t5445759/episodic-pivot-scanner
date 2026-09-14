#!/usr/bin/env python
"""Entry point for running the web API server."""
import uvicorn
import sys

if __name__ == "__main__":
    # Run the FastAPI server
    # Usage: python run_api.py [--host HOST] [--port PORT] [--reload]
    
    host = "0.0.0.0"
    port = 8000
    reload = "--reload" in sys.argv
    
    print("\n" + "="*80)
    print("🚀 Starting Episodic Pivot Scanner API")
    print("="*80)
    print(f"\n📡 API Server: http://{host}:{port}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    print(f"🎨 Dashboard: http://localhost:{port}/dashboard")
    print(f"\nReload: {reload}\n")
    
    uvicorn.run(
        "src.web.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
