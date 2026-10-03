import json
import re
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import httpx
from . import config


@dataclass
class Generation:
    source: str
    elapsed_ms: int
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: str | None = None


class AgentError(Exception):
    pass


def available_agents():
    return [
        dict(
            id="reference",
            name="Reference implementation",
            kind="Authored baseline",
            available=True,
            description="Known-correct fixtures. Validates the evaluation pipeline; not an AI model.",
        ),
        dict(
            id="naive",
            name="Naive implementation",
            kind="Authored baseline",
            available=True,
            description="Deliberately incomplete fixtures that expose common edge-case failures.",
        ),
        dict(
            id="provider",
            name=config.PROVIDER_MODEL or "Model provider",
            kind="OpenAI-compatible API",
            available=bool(
                config.PROVIDER_BASE_URL and config.PROVIDER_MODEL and config.PROVIDER_API_KEY
            ),
            description="Generates Python from the task prompt using your server-configured model.",
        ),
    ]


def token_count(value):
    return value if type(value) is int and 0 <= value <= 100_000_000 else None


def cost(input_tokens, output_tokens):
    if (
        input_tokens is None
        or output_tokens is None
        or not config.INPUT_PRICE
        or not config.OUTPUT_PRICE
    ):
        return None
    try:
        prices = [Decimal(config.INPUT_PRICE), Decimal(config.OUTPUT_PRICE)]
        if any(not p.is_finite() or p < 0 for p in prices):
            return None
        return str((input_tokens * prices[0] + output_tokens * prices[1]) / Decimal(1_000_000))
    except InvalidOperation:
        return None


def generate(agent, task):
    start = time.monotonic()
    if agent in ("reference", "naive"):
        return Generation(
            task[agent], round((time.monotonic() - start) * 1000), "authored-" + agent
        )
    if agent != "provider" or not available_agents()[2]["available"]:
        raise AgentError("Model provider is not configured")
    prompt = (
        task["prompt"]
        + "\nStarter:\n"
        + task["starter"]
        + "\nExample input/output:\n"
        + json.dumps(task["cases"][:1])
    )
    try:
        with httpx.Client(timeout=45, trust_env=False, follow_redirects=False) as client:
            with client.stream(
                "POST",
                config.PROVIDER_BASE_URL.rstrip("/") + "/chat/completions",
                headers={"Authorization": "Bearer " + config.PROVIDER_API_KEY},
                json={
                    "model": config.PROVIDER_MODEL,
                    "temperature": 0,
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Return only a Python source file implementing the requested function. No explanations. No tools or network access.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
            ) as response:
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 256_000:
                        raise AgentError("Provider response exceeds 256 KB")
                data = json.loads(body)
        source = data["choices"][0]["message"]["content"]
        if not isinstance(source, str) or not source.strip() or len(source.encode()) > 64_000:
            raise AgentError("Provider did not return a valid source file")
        match = re.fullmatch(r"\s*```(?:python)?\s*\n(.*?)\n```\s*", source, re.S)
        source = match.group(1) if match else source
        usage = data.get("usage") or {}
        inp, out = (
            token_count(usage.get("prompt_tokens")),
            token_count(usage.get("completion_tokens")),
        )
        return Generation(
            source,
            round((time.monotonic() - start) * 1000),
            str(data.get("model", config.PROVIDER_MODEL))[:200],
            inp,
            out,
            cost(inp, out),
        )
    except AgentError:
        raise
    except (httpx.HTTPError, KeyError, ValueError, TypeError, IndexError, AttributeError):
        # Do not persist response text: it can include provider keys or private data.
        raise AgentError("Provider request failed or returned an invalid response") from None
