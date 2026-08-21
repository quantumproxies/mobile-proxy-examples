"""Which carriers and ASNs am I actually exiting through?

Mobile pools are not uniform. Knowing the ASN mix tells you whether "mobile US"
means three carriers or thirty, which matters when a target blocks by ASN.

    export QD_PROXY_USER=... QD_PROXY_PASS=...
    python3 carrier_check.py --country us --n 12
"""
from __future__ import annotations

import argparse
import os
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import requests

GATEWAY = "mb.quanticdata.io:7777"
CHECK = "https://ipinfo.io/json"

USER = os.environ.get("QD_PROXY_USER") or ""
PASS = os.environ.get("QD_PROXY_PASS") or ""
if not (USER and PASS):
    raise SystemExit("set QD_PROXY_USER and QD_PROXY_PASS")


def probe(country: str) -> dict:
    url = f"http://{USER}-country-{country}:{PASS}@{GATEWAY}"
    try:
        return requests.get(CHECK, proxies={"http": url, "https": url}, timeout=45).json()
    except requests.RequestException as exc:
        return {"error": str(exc)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="us")
    ap.add_argument("--n", type=int, default=10)
    args = ap.parse_args()

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: probe(args.country), range(args.n)))

    ok = [r for r in results if r.get("ip")]
    failed = [r for r in results if r.get("error")]
    print(f"{len(ok)}/{args.n} requests succeeded"
          + (f", {len(failed)} failed" if failed else ""))
    if failed:
        print(f"  first error: {failed[0]['error'][:110]}")
    if not ok:
        return

    print(f"{len(set(r['ip'] for r in ok))} distinct exit IPs\n")

    carriers = Counter()
    asns = Counter()
    for row in ok:
        org = row.get("org") or ""
        match = re.match(r"(AS\d+)\s+(.*)", org)
        if match:
            asns[match.group(1)] += 1
            carriers[match.group(2)] += 1
        elif org:
            carriers[org] += 1

    print("carriers")
    for carrier, n in carriers.most_common():
        print(f"  {n:>3}  {carrier}")

    print("\nASNs")
    for asn, n in asns.most_common():
        print(f"  {n:>3}  {asn}")

    print("\ncities")
    for city, n in Counter(f"{r.get('city')}, {r.get('region')}" for r in ok).most_common(10):
        print(f"  {n:>3}  {city}")

    countries = Counter(r.get("country") for r in ok)
    if set(countries) - {args.country.upper()}:
        print(f"\n⚠ exits outside {args.country.upper()}: "
              f"{ {k: v for k, v in countries.items() if k != args.country.upper()} }")


if __name__ == "__main__":
    main()
