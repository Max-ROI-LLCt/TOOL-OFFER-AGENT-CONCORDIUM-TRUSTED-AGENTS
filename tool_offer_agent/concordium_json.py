"""Strict, detached JSON for the Concordium boundary, not existing commerce."""

from hashlib import sha256
import json


MAX_SAFE_INTEGER = 2**53 - 1


def canonical(value):
    def check(item, depth=0):
        if depth > 32:
            raise ValueError("JSON nesting exceeds boundary limit")
        if item is None or type(item) is bool:
            return
        if type(item) is str:
            item.encode("utf-8", errors="strict")
        elif type(item) is int and abs(item) <= MAX_SAFE_INTEGER:
            return
        elif type(item) is list:
            for entry in item:
                check(entry, depth + 1)
        elif type(item) is dict and all(type(key) is str for key in item):
            for key, entry in item.items():
                check(key, depth + 1)
                check(entry, depth + 1)
        else:
            raise ValueError("Strict JSON required; use strings for decimal amounts")

    check(value)
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False)
    if len(encoded.encode("utf-8")) > 524288:
        raise ValueError("JSON exceeds boundary limit")
    return encoded


def snapshot(value):
    return json.loads(canonical(value))


def digest(value):
    return sha256(canonical(value).encode("utf-8")).hexdigest()
