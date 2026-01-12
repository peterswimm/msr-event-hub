#!/usr/bin/env python3
"""Development server startup script for Knowledge Agent API.

Run with: python3 run_server.py
Or with options: python3 run_server.py --port 9000 --data ./custom_data
"""

import argparse
import sys
from pathlib import Path

try:
    from main import create_app, HAS_FASTAPI
except ImportError as e:
    print(f"Failed to import main module: {e}")
    sys.exit(1)

if not HAS_FASTAPI:
    print("ERROR: FastAPI is required to run the server.")
    print("Install with: pip install fastapi uvicorn")
    sys.exit(1)


def main():
    """Parse arguments and run the server."""
    parser = argparse.ArgumentParser(
        description="Run the Knowledge Agent API server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run server on (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("./data"),
        help="Data storage root directory (default: ./data)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on file changes (development mode)"
    )
    parser.add_argument(
        "--log-level",
        choices=["critical", "error", "warning", "info", "debug"],
        default="info",
        help="Logging level (default: info)"
    )
    
    args = parser.parse_args()
    
    # Create application
    app = create_app(storage_root=args.data)
    if app is None:
        print("ERROR: Failed to create application")
        sys.exit(1)
    
    # Run with uvicorn
    try:
        import uvicorn
    except ImportError:
        print("ERROR: uvicorn is required to run the server.")
        print("Install with: pip install uvicorn")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("Knowledge Agent API Server")
    print(f"{'='*60}")
    print(f"  URL: http://{args.host}:{args.port}")
    print(f"  Docs: http://{args.host}:{args.port}/docs")
    print(f"  Data: {args.data}")
    print(f"  Mode: {'Development (auto-reload)' if args.reload else 'Production'}")
    print(f"{'='*60}\n")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()
