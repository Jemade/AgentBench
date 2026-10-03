"""Execute candidate functions. External code is Docker-only, never local."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
from . import config

HARNESS = """import copy, importlib.util, json, sys
spec = importlib.util.spec_from_file_location("candidate", "/workspace/solution.py" if len(sys.argv)==1 else sys.argv[1])
module = importlib.util.module_from_spec(spec)
rows=[]
try:
    spec.loader.exec_module(module)
    cases=json.load(open("/workspace/cases.json" if len(sys.argv)==1 else sys.argv[2]))
    for i, pair in enumerate(cases):
        value, expected = pair
        original=copy.deepcopy(value)
        try:
            actual=module.solve(value)
            valid=actual == expected and value == original and type(actual) is type(expected)
            rows.append({"index":i+1,"passed":valid,"expected":expected,"actual":actual,"mutated_input":value != original})
        except Exception as e:
            rows.append({"index":i+1,"passed":False,"error":type(e).__name__})
except Exception as e:
    print("AGENTBENCH_RESULT="+json.dumps({"error":type(e).__name__}))
    sys.exit(1)
print("AGENTBENCH_RESULT="+json.dumps({"cases":rows},default=lambda x:"<non-JSON value>"))
"""


class RunnerError(Exception):
    pass


def readiness():
    if config.RUNNER == "trusted-local":
        return dict(
            mode="trusted-local",
            ready=config.ALLOW_TRUSTED_LOCAL,
            detail="Only exact authored baseline sources may execute locally.",
        )
    if config.RUNNER != "docker":
        return dict(mode=config.RUNNER, ready=False, detail="Unknown runner mode")
    try:
        r = subprocess.run(
            ["docker", "image", "inspect", config.SANDBOX_IMAGE], capture_output=True, timeout=5
        )
        return dict(
            mode="docker",
            ready=r.returncode == 0,
            detail="Sandbox image ready"
            if r.returncode == 0
            else "Build the sandbox image and start Docker",
        )
    except (OSError, subprocess.TimeoutExpired):
        return dict(mode="docker", ready=False, detail="Docker is unavailable to the worker")


def evaluate(source, task, agent):
    local = config.RUNNER == "trusted-local"
    if local and (
        not config.ALLOW_TRUSTED_LOCAL
        or agent not in ("reference", "naive")
        or source != task[agent]
    ):
        raise RunnerError("Local runner refuses all non-baseline source")
    if not local and config.RUNNER != "docker":
        raise RunnerError("Unknown runner mode")
    start = time.monotonic()
    name = "agentbench-" + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="agentbench-") as directory:
        root = Path(directory)
        (root / "solution.py").write_text(source)
        (root / "cases.json").write_text(json.dumps(task["cases"]))
        (root / "harness.py").write_text(HARNESS)
        for path in root.iterdir():
            path.chmod(0o644)
        root.chmod(0o755)
        if local:
            command = [
                sys.executable,
                "-I",
                "-B",
                str(root / "harness.py"),
                str(root / "solution.py"),
                str(root / "cases.json"),
            ]
        else:
            command = [
                "docker",
                "run",
                "--rm",
                "--name",
                name,
                "--network=none",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--pids-limit=64",
                "--memory=128m",
                "--memory-swap=128m",
                "--cpus=0.5",
                "--ulimit",
                "nofile=64:64",
                "--user",
                "65534:65534",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=16m",
                "--mount",
                f"type=bind,source={root},target=/workspace,readonly",
                config.SANDBOX_IMAGE,
                "python",
                "-I",
                "-B",
                "/workspace/harness.py",
            ]
        try:
            # File-backed output prevents hostile stdout from consuming host RAM.
            with (root / "output.log").open("w+b") as output:
                process = subprocess.Popen(
                    command,
                    stdout=output,
                    stderr=output,
                    env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/tmp"},
                )
                deadline = time.monotonic() + 10
                exceeded = False
                while process.poll() is None:
                    if (
                        time.monotonic() > deadline
                        or output.tell() > 256_000
                        or (root / "output.log").stat().st_size > 256_000
                    ):
                        exceeded = True
                        process.kill()
                        process.wait(timeout=5)
                        break
                    time.sleep(0.025)
                output.seek(0)
                text = output.read(256_000).decode("utf-8", errors="replace")
            elapsed = round((time.monotonic() - start) * 1000)
            if exceeded:
                return dict(
                    state="failed",
                    passed=0,
                    total=len(task["cases"]),
                    execution_ms=elapsed,
                    cases=[],
                    error="Execution time or output limit exceeded",
                )
            if not local and process.returncode in (125, 126, 127):
                raise RunnerError("Docker could not start the sandbox; check image and daemon")
            lines = [line for line in text.splitlines() if line.startswith("AGENTBENCH_RESULT=")]
            if not lines:
                return dict(
                    state="failed",
                    passed=0,
                    total=len(task["cases"]),
                    execution_ms=elapsed,
                    cases=[],
                    error="Candidate exited without test results",
                )
            try:
                result = json.loads(lines[-1].split("=", 1)[1])
                if "error" in result:
                    return dict(
                        state="failed",
                        passed=0,
                        total=len(task["cases"]),
                        execution_ms=elapsed,
                        cases=[],
                        error="Candidate error: " + str(result["error"])[:200],
                    )
                cases = result["cases"]
                if len(cases) != len(task["cases"]) or any(
                    type(c.get("passed")) is not bool for c in cases
                ):
                    raise ValueError
                return dict(
                    state="scored",
                    passed=sum(c["passed"] for c in cases),
                    total=len(cases),
                    execution_ms=elapsed,
                    cases=cases,
                    error=None,
                )
            except (ValueError, KeyError, TypeError):
                return dict(
                    state="failed",
                    passed=0,
                    total=len(task["cases"]),
                    execution_ms=elapsed,
                    cases=[],
                    error="Invalid test output",
                )
        except OSError:
            raise RunnerError("Runner executable is unavailable") from None
        finally:
            if not local:
                try:
                    subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    pass
