"""Versioned, authored Python benchmark fixtures. Baselines are not AI models."""

import hashlib
import json

TASKS = [
    dict(
        id="merge-intervals",
        title="Merge overlapping intervals",
        category="Algorithms",
        difficulty="Intermediate",
        entrypoint="solve",
        prompt="Implement solve(intervals). Return sorted merged closed intervals as lists. Merge touching intervals. Never mutate input. Empty input returns [].",
        starter="def solve(intervals):\n    raise NotImplementedError\n",
        cases=[
            ([[5, 7], [1, 3], [2, 4]], [[1, 4], [5, 7]]),
            ([], []),
            ([[1, 2], [2, 3]], [[1, 3]]),
            ([[1, 9], [2, 3]], [[1, 9]]),
            ([[4, 4]], [[4, 4]]),
            ([[-3, -1], [-2, 2], [8, 9]], [[-3, 2], [8, 9]]),
        ],
        reference="""def solve(intervals):
    result = []
    for start, end in sorted(intervals):
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result
""",
        naive="def solve(intervals):\n    return sorted(intervals)\n",
    ),
    dict(
        id="money-to-cents",
        title="Parse money without float drift",
        category="Data integrity",
        difficulty="Intermediate",
        entrypoint="solve",
        prompt="Implement solve(value). Parse a decimal string into integer cents. Accept whitespace, signed values and at most two fractional digits. Invalid, non-finite, or excess fractional digits must return None. Do not use float rounding.",
        starter="def solve(value):\n    raise NotImplementedError\n",
        cases=[
            ("12.34", 1234),
            (" 0.29 ", 29),
            ("-2.50", -250),
            ("0", 0),
            ("1.001", None),
            ("NaN", None),
            ("bad", None),
            ("999999.99", 99999999),
        ],
        reference="""from decimal import Decimal, InvalidOperation
def solve(value):
    try:
        amount = Decimal(value.strip())
        if not amount.is_finite() or amount.as_tuple().exponent < -2:
            return None
        return int(amount * 100)
    except (InvalidOperation, ValueError, AttributeError):
        return None
""",
        naive="""def solve(value):
    try:
        return round(float(value) * 100)
    except (ValueError, OverflowError):
        return None
""",
    ),
    dict(
        id="stable-dedup",
        title="Deduplicate event deliveries",
        category="Backend",
        difficulty="Foundational",
        entrypoint="solve",
        prompt="Implement solve(events). Keep the first event for each id in original order. Events without id must each be kept. A null id counts as missing. Do not mutate any input.",
        starter="def solve(events):\n    raise NotImplementedError\n",
        cases=[
            (
                [{"id": "a", "v": 1}, {"id": "a", "v": 2}, {"id": "b"}],
                [{"id": "a", "v": 1}, {"id": "b"}],
            ),
            ([], []),
            ([{"v": 1}, {"v": 2}], [{"v": 1}, {"v": 2}]),
            ([{"id": None}, {"id": None}], [{"id": None}, {"id": None}]),
            ([{"id": 0}, {"id": 0}, {"id": 1}], [{"id": 0}, {"id": 1}]),
        ],
        reference="""def solve(events):
    seen, result = set(), []
    for event in events:
        key = event.get('id')
        if key is None or key not in seen:
            result.append(event.copy())
            if key is not None:
                seen.add(key)
    return result
""",
        naive="""def solve(events):
    return list({e.get('id'): e for e in events}.values())
""",
    ),
    dict(
        id="retry-policy",
        title="Classify retryable HTTP errors",
        category="Reliability",
        difficulty="Foundational",
        entrypoint="solve",
        prompt="Implement solve(request). request has status and attempt (1-based). Return {retry: bool, delay: integer seconds}. Retry only 408, 429, and 500..599 when attempt < 4. Delay for a retry is 2**attempt capped at 30. For no retry return delay 0.",
        starter="def solve(request):\n    raise NotImplementedError\n",
        cases=[
            ({"status": 503, "attempt": 1}, {"retry": True, "delay": 2}),
            ({"status": 429, "attempt": 3}, {"retry": True, "delay": 8}),
            ({"status": 408, "attempt": 2}, {"retry": True, "delay": 4}),
            ({"status": 400, "attempt": 1}, {"retry": False, "delay": 0}),
            ({"status": 503, "attempt": 4}, {"retry": False, "delay": 0}),
            ({"status": 200, "attempt": 1}, {"retry": False, "delay": 0}),
        ],
        reference="""def solve(request):
    retry = (request['status'] in (408, 429) or 500 <= request['status'] <= 599) and request['attempt'] < 4
    return {'retry': retry, 'delay': min(2 ** request['attempt'], 30) if retry else 0}
""",
        naive="""def solve(request):
    retry = request['status'] >= 500
    return {'retry': retry, 'delay': 2 if retry else 0}
""",
    ),
    dict(
        id="redact-secrets",
        title="Redact nested sensitive fields",
        category="Security",
        difficulty="Intermediate",
        entrypoint="solve",
        prompt="Implement solve(value). Recursively copy JSON dictionaries/lists, replacing values under keys password, token, api_key (case-insensitive exact match) with [REDACTED]. Preserve other values and never mutate input.",
        starter="def solve(value):\n    raise NotImplementedError\n",
        cases=[
            ({"password": "x", "name": "Jayden"}, {"password": "[REDACTED]", "name": "Jayden"}),
            (
                {"data": [{"TOKEN": "x"}, {"api_key": "y"}]},
                {"data": [{"TOKEN": "[REDACTED]"}, {"api_key": "[REDACTED]"}]},
            ),
            ([1, "x", None], [1, "x", None]),
            ({"access_token": "x"}, {"access_token": "x"}),
            ({"PASSWORD": {"secret": "x"}}, {"PASSWORD": "[REDACTED]"}),
        ],
        reference="""def solve(value):
    if isinstance(value, dict):
        return {k: '[REDACTED]' if k.lower() in {'password','token','api_key'} else solve(v) for k,v in value.items()}
    if isinstance(value, list):
        return [solve(v) for v in value]
    return value
""",
        naive="""def solve(value):
    if isinstance(value, dict):
        return {k: '[REDACTED]' if k == 'password' else v for k,v in value.items()}
    return value
""",
    ),
    dict(
        id="page-window",
        title="Return a bounded page window",
        category="API design",
        difficulty="Foundational",
        entrypoint="solve",
        prompt="Implement solve(request). request has items (list), page (1-based), size (>0). Return {items: slice, total: length, pages: ceiling(total/size)}. Invalid page or size returns None. An out-of-range page returns an empty items list. Do not mutate input.",
        starter="def solve(request):\n    raise NotImplementedError\n",
        cases=[
            (
                {"items": [1, 2, 3, 4, 5], "page": 2, "size": 2},
                {"items": [3, 4], "total": 5, "pages": 3},
            ),
            ({"items": [], "page": 1, "size": 2}, {"items": [], "total": 0, "pages": 0}),
            ({"items": [1], "page": 3, "size": 2}, {"items": [], "total": 1, "pages": 1}),
            ({"items": [1], "page": 0, "size": 2}, None),
            ({"items": [1], "page": 1, "size": 0}, None),
            (
                {"items": [1, 2, 3], "page": 1, "size": 3},
                {"items": [1, 2, 3], "total": 3, "pages": 1},
            ),
        ],
        reference="""def solve(request):
    items, page, size = request['items'], request['page'], request['size']
    if page < 1 or size < 1:
        return None
    return {'items': items[(page-1)*size:page*size], 'total':len(items), 'pages':(len(items)+size-1)//size}
""",
        naive="""def solve(request):
    items, page, size = request['items'], request['page'], request['size']
    if size < 1:
        return None
    return {'items':items[page*size:(page+1)*size], 'total':len(items), 'pages':len(items)//size}
""",
    ),
]

VERSION = "python-core-1.0.0"


def fingerprint(tasks):
    return hashlib.sha256(
        json.dumps(tasks, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def snapshot(ids):
    return [t for t in TASKS if t["id"] in ids]


def public_task(task):
    return {k: v for k, v in task.items() if k not in ("reference", "naive", "cases")} | {
        "test_count": len(task["cases"]),
        "examples": task["cases"][:1],
    }
