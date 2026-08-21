"""Is the mobile tier actually buying you anything on THIS target?

Runs the same URL through mobile, residential and datacenter exits and reports
success rate, median latency and what the failures looked like. Run it before you
budget for mobile bandwidth, not after.

    python3 mobile_vs_resi.py https://target.example --n 8 --country us
"""
from __future__ import annotations

import argparse
import os
import statistics
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import requests

GATEWAYS = {
    "mobile": "mb.quanticdata.io:7777",
    "residential": "pr.quanticdata.io:7777",
    "datacenter": "dc.quanticdata.io:7777",
}

USER = os.environ.get("QD_PROXY_USER") or ""
PASS = os.environ.get("QD_PROXY_PASS") or ""
if not (USER and PASS):
    raise SystemExit("set QD_PROXY_USER and QD_PROXY_PASS")

MOBILE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
DESKTOP_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")


def attempt(tier: str, url: str, country: str) -> dict:
    proxy = f"http://{USER}-country-{country}:{PASS}@{GATEWAYS[tier]}"
    # Coherence: a mobile exit gets a mobile user-agent, not a desktop one.
    ua = MOBILE_UA if tier == "mobile" else DESKTOP_UA
    started = time.perf_counter()
    try:
        r = requests.get(url, proxies={"http": proxy, "https": proxy},
                         headers={"User-Agent": ua}, timeout=60)
        return {"tier": tier, "status": r.status_code, "bytes": len(r.content),
                "seconds": time.perf_counter() - started}
    except requests.RequestException as exc:
        return {"tier": tier, "status": None, "error": type(exc).__name__,
                "seconds": time.perf_counter() - started}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--country", default="us")
    ap.add_argument("--n", type=int, default=6, help="attempts per tier")
    args = ap.parse_args()

    jobs = [(tier, args.url, args.country) for tier in GATEWAYS for _ in range(args.n)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda j: attempt(*j), jobs))

    print(f"{args.url}   {args.n} attempts per tier, exit {args.country.upper()}\n")
    print(f"{'tier':<14}{'ok':>6}{'median s':>10}{'median KB':>11}  statuses")
    for tier in GATEWAYS:
        rows = [r for r in results if r["tier"] == tier]
        good = [r for r in rows if r.get("status") == 200]
        latency = statistics.median([r["seconds"] for r in rows])
        size = statistics.median([r["bytes"] for r in good]) / 1024 if good else 0
        codes = Counter(r.get("status") or r.get("error") for r in rows)
        print(f"{tier:<14}{len(good):>3}/{len(rows):<2}{latency:>10.1f}{size:>11.0f}  "
              f"{dict(codes)}")

    mobile_ok = sum(1 for r in results if r["tier"] == "mobile" and r.get("status") == 200)
    resi_ok = sum(1 for r in results if r["tier"] == "residential" and r.get("status") == 200)
    print()
    if mobile_ok > resi_ok:
        print("Mobile wins here — the target is treating carrier ASNs differently.")
    elif resi_ok >= mobile_ok and resi_ok > 0:
        print("Residential does the job. Mobile bandwidth would be money spent on nothing "
              "for this target.")
    else:
        print("Neither tier got through cleanly — this is a rendering or fingerprint problem, "
              "not an exit problem. Try https://quanticdata.io/web-scraping-api/")


if __name__ == "__main__":
    main()
