#!/usr/bin/env python3
"""
Pre-traffic smoke test: hit /health/ready on a specific Cloud Run revision URL
and assert it returns 200 with {"status": "ok"}.

Called by the deploy workflow after --no-traffic deploy and before traffic switch.
"""

import argparse
import json
import sys
import time
import urllib.request
from urllib.parse import urlparse


def smoke_test(revision_url: str, path: str, retries: int = 10, delay: float = 5.0) -> None:
    parsed_revision_url = urlparse(revision_url)
    if parsed_revision_url.scheme != "https" or not parsed_revision_url.hostname:
        raise ValueError("--revision-url must be an absolute HTTPS URL")

    target = f"{revision_url.rstrip('/')}{path}"
    print(f"Smoke testing: {target}")

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(  # noqa: S310 -- HTTPS validated above
                target,
                headers={"User-Agent": "financial-os-smoke-test/1"},
            )
            with urllib.request.urlopen(  # noqa: S310 -- HTTPS validated above
                req, timeout=10
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}")
                body = json.loads(resp.read())
                if body.get("status") != "ok":
                    raise RuntimeError(f"Unexpected body: {body!r}")
                print(f"PASS (attempt {attempt}): {path} → status=ok")
                return
        except Exception as exc:
            last_error = exc
            print(f"Attempt {attempt}/{retries} failed: {exc}", file=sys.stderr)
            if attempt < retries:
                time.sleep(delay)

    print(
        f"FAIL: smoke test did not pass after {retries} attempts. Last error: {last_error}",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision-url", required=True)
    parser.add_argument("--path", default="/health/ready")
    parser.add_argument("--retries", type=int, default=10)
    parser.add_argument("--delay", type=float, default=5.0)
    args = parser.parse_args()
    smoke_test(args.revision_url, args.path, args.retries, args.delay)
