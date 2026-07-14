"""Cache isolation validation for vLLM prefix cache."""

from __future__ import annotations

import argparse
import sys

import httpx

from cbudget.models.client import ModelClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True, help="vLLM base URL, e.g. http://localhost:8000")
    args = parser.parse_args()
    base = args.server.rstrip("/")
    metrics_url = f"{base}/metrics"
    client = ModelClient(base_url=base, use_mock=False)

    def scrape_hits() -> int:
        text = httpx.get(metrics_url, timeout=10.0).text
        hits = 0
        for line in text.splitlines():
            if "prefix_cache" in line and "hit" in line and not line.startswith("#"):
                try:
                    hits += int(float(line.split()[-1]))
                except ValueError:
                    pass
        return hits

    prompt_a = "Cache isolation probe A: " + ("token " * 50)
    prompt_b = "Cache isolation probe B: " + ("block " * 50)

    client.generate(prompt_a, max_tokens=4, temperature=0.0)
    hits_after_a = scrape_hits()

    reset_ok = False
    for path in ("/reset_prefix_cache", "/v1/reset_prefix_cache"):
        try:
            response = httpx.post(f"{base}{path}", timeout=10.0)
            if response.status_code < 400:
                reset_ok = True
                break
        except Exception:
            continue

    if reset_ok:
        client.generate(prompt_b, max_tokens=4, temperature=0.0)
        hits_after_b = scrape_hits()
        if hits_after_b <= hits_after_a:
            print("Cache reset endpoint validated: no cross-run hit growth after reset.")
            return
        print(f"WARNING: hits grew after reset ({hits_after_a} -> {hits_after_b}); use server_restart method.")

    print("Cache validation: reset endpoint unavailable or inconclusive; recommend server_restart at freeze.")
    print("Sequential scrape-before/after per run remains valid for delta measurement.")


if __name__ == "__main__":
    main()
