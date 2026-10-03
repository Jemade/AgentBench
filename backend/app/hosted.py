"""Supervise the API and demo workers as one hosted service."""

import os
import signal
import subprocess
import sys
import threading

from . import config


def supervise(commands):
    """Stop every child on shutdown or when any component exits."""
    stop = threading.Event()
    children = []

    def shutdown(signum, frame):
        stop.set()

    previous = {sig: signal.signal(sig, shutdown) for sig in (signal.SIGTERM, signal.SIGINT)}
    result = 0
    try:
        for command in commands:
            if stop.is_set():
                break
            children.append(subprocess.Popen(command))
        while not stop.wait(0.25):
            for child in children:
                status = child.poll()
                if status is not None:
                    print("Hosted component exited; stopping service.", flush=True)
                    result = status or 1
                    stop.set()
                    break
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    return result


def api_command():
    port = int(os.getenv("PORT", "10000"))
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    return [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(port)]


def main():
    from .seed import main as seed

    embedded = os.getenv("HOSTED_WORKER", "true").lower() == "true"
    if embedded and (config.RUNNER != "trusted-local" or not config.ALLOW_TRUSTED_LOCAL):
        raise ValueError("Embedded hosted worker supports authored trusted-local baselines only")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    seed()
    commands = [api_command()]
    if embedded:
        commands.insert(0, [sys.executable, "-m", "app.worker"])
    return supervise(commands)


if __name__ == "__main__":
    raise SystemExit(main())

