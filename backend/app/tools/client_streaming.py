#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tool_client_streaming.py - Command-line client for backend API streaming via SSE.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional
from urllib import error, request

API_BASE = "http://localhost:8000"


def read_prompt(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        sys.stderr.write(f"Error: file {path} does not exist.\n")
        sys.exit(1)
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"Error: reading file {path}: {e}\n")
        sys.exit(1)


def post_prompt(prompt: str) -> str:
    url = f"{API_BASE}/main"
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    req = request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=10) as response:
            body = response.read()
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        sys.stderr.write(f"POST {url} failed: {e.code} - {e.reason}\n{detail}\n")
        sys.exit(1)
    except error.URLError as e:
        sys.stderr.write(f"POST {url} failed: {e}\n")
        sys.exit(1)

    try:
        obj = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Invalid JSON from server: {e}\n")
        sys.exit(1)

    sid = obj.get("session_id")
    if not isinstance(sid, str) or not sid:
        sys.stderr.write(f"'session_id' missing in response: {obj}\n")
        sys.exit(1)

    return sid


def stream_events(session_id: str) -> None:
    url = f"{API_BASE}/main/stream/{session_id}"
    headers = {
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
    }
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req) as response:
            for raw in response:
                line = raw.decode("utf-8", errors="replace")
                sys.stdout.write(line)
                sys.stdout.flush()
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        sys.stderr.write(f"Streaming {url} failed: {e.code} - {e.reason}\n{detail}\n")
        sys.exit(1)
    except error.URLError as e:
        sys.stderr.write(f"Streaming {url} failed: {e}\n")
        sys.exit(1)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Frontal API client")
    parser.add_argument("-f", "--file", required=True, help="Path to the prompt file")
    args = parser.parse_args(argv)

    prompt = read_prompt(args.file)
    session_id = post_prompt(prompt)
    stream_events(session_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
