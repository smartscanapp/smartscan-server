#!/usr/bin/env python3

import argparse
import uvicorn
from server.app import app

def main():
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port for server")
    parser.add_argument("--workers", "-w", type=int, default=0, help="Server workers")

    args, _ = parser.parse_known_args()

    uvicorn.run(app, port=args.port, workers=args.workers)
   
if __name__ == "__main__":
    main()
