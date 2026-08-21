# Mobile proxy examples — 4G/5G carrier exits, and when they are worth the price

A [mobile proxy](https://quanticdata.io/mobile-proxies/) exits through a real cellular carrier,
so the IP belongs to a mobile ASN behind carrier-grade NAT — shared, at any moment, with a large
number of ordinary phone users. That shared-fate property is the entire product: blocking the IP
means blocking real customers, so sites are far more reluctant to do it.

Gateway: `mb.quanticdata.io:7777`

```bash
export QD_PROXY_USER=your_user QD_PROXY_PASS=your_pass
python3 carrier_check.py --country us --n 10     # which ASNs am I actually getting?
python3 mobile_vs_resi.py https://target.example  # is the mobile tier buying you anything?
node app_api.mjs                                  # mobile-shaped headers for a mobile API
```

## Files

| File | What it does |
|---|---|
| [`carrier_check.py`](carrier_check.py) | exit ASN, carrier and geo distribution over N requests |
| [`mobile_vs_resi.py`](mobile_vs_resi.py) | same URL through mobile, residential and datacenter — success rate and latency |
| [`app_api.mjs`](app_api.mjs) | calling a mobile app's own API with a coherent mobile fingerprint |

## Credentials and targeting

```bash
# rotating mobile exit in the US
curl -x mb.quanticdata.io:7777 -U "USER-country-us:PASS" https://ipinfo.io/json

# hold one carrier IP for 15 minutes
curl -x mb.quanticdata.io:7777 \
     -U "USER-country-gb-session-b41c-sessTime-15:PASS" https://ipinfo.io/json
```

Same username-modifier syntax as every other QuanticData network — see
[quanticdata-proxy-quickstart](https://github.com/quantumproxies/quanticdata-proxy-quickstart)
for the full list.

## When mobile is the right tool

**Yes:** mobile-only or mobile-first apps and their APIs; targets that block datacenter and
residential ranges but leave carrier ASNs alone; anything where the block risk of a shared IP is
the point.

**No:** ordinary page scraping at volume. Mobile bandwidth is the most expensive tier by a wide
margin, and for most targets [residential](https://quanticdata.io/residential-proxies/) —
or the [Web Scraping API](https://quanticdata.io/web-scraping-api/), which picks the tier for
you — gets the same page for a fraction of the cost.

`mobile_vs_resi.py` exists to settle that question with numbers on *your* target rather than
with a vendor's opinion.

## Two things people get wrong

**Latency is higher, and that is normal.** A cellular hop adds real milliseconds. Raise your
timeouts instead of retrying a request that was going to succeed.

**A mobile IP with a desktop fingerprint is a contradiction.** If you exit through a carrier ASN
while sending a desktop Chrome user-agent and a 1920×1080 viewport, you have made yourself *more*
identifiable, not less. `app_api.mjs` shows the coherent version.

## Related

- [Mobile proxies](https://quanticdata.io/mobile-proxies/) · [Residential proxies](https://quanticdata.io/residential-proxies/) · [Rotating proxies](https://quanticdata.io/rotating-proxies/)
- [How to detect residential proxies](https://quanticdata.io/blog/how-to-detect-residential-proxies/) · [How can residential proxies be legal?](https://quanticdata.io/blog/how-can-residential-proxies-be-legal/)
- [Is browser fingerprinting legal?](https://quanticdata.io/blog/is-browser-fingerprinting-legal/) · [Is device fingerprinting legal?](https://quanticdata.io/blog/is-device-fingerprinting-legal/)

MIT licensed.
