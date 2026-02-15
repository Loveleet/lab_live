#!/usr/bin/env python3
"""
Run the Node API server (server.js). Use this when you can trigger a Python file
automatically but not a Node command directly.
"""
import os
import sys
import subprocess

# Project root = directory where this script lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_JS = os.path.join(SCRIPT_DIR, "server", "server.js")


def main():
    if not os.path.isfile(SERVER_JS):
        print(f"Error: server.js not found at {SERVER_JS}", file=sys.stderr)
        sys.exit(1)

    os.chdir(SCRIPT_DIR)
    cmd = ["node", "server/server.js"]
    print(f"[run_node_server] Starting: {' '.join(cmd)} in {SCRIPT_DIR}")
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("Error: 'node' not found. Install Node.js and ensure it is in PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
