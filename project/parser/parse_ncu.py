from __future__ import annotations

from typing import Any


def parse_key_value_output(text: str) -> dict[str, Any]:
    """
    Parse simple key=value lines from benchmark stdout.
    Example:
        avg_time_ms=0.123
        effective_bandwidth_gb_s=456.7
    """
    result: dict[str, Any] = {}

    for line in text.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Try int, then float, then raw string
        try:
            result[key] = int(value)
            continue
        except ValueError:
            pass

        try:
            result[key] = float(value)
            continue
        except ValueError:
            pass

        result[key] = value

    return result
