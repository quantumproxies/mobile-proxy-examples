/**
 * Calling a mobile app's own API through a carrier exit — coherently.
 *
 * The exit IP is only one signal. A carrier ASN paired with a desktop user-agent,
 * a desktop Accept-Language and no mobile client headers is a *more* distinctive
 * fingerprint than either half alone. Keep the story consistent.
 *
 *   QD_PROXY_USER=... QD_PROXY_PASS=... node app_api.mjs
 */
import { ProxyAgent } from "undici";

const USER = process.env.QD_PROXY_USER;
const PASS = process.env.QD_PROXY_PASS;
if (!USER || !PASS) {
  console.error("set QD_PROXY_USER and QD_PROXY_PASS");
  process.exit(1);
}

const GATEWAY = "mb.quanticdata.io:7777";

/** One coherent device story: Android phone, Chrome, matching client hints. */
const ANDROID = {
  "User-Agent":
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) " +
    "Chrome/140.0.0.0 Mobile Safari/537.36",
  "Accept-Language": "en-US,en;q=0.9",
  "sec-ch-ua": '"Chromium";v="140", "Google Chrome";v="140", "Not?A_Brand";v="24"',
  "sec-ch-ua-mobile": "?1",
  "sec-ch-ua-platform": '"Android"',
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Site": "same-origin",
};

function agent({ country = "us", session, minutes } = {}) {
  const parts = [USER, "country", country];
  if (session) parts.push("session", session);
  if (minutes) parts.push("sessTime", String(minutes));
  return new ProxyAgent(
    `http://${encodeURIComponent(parts.join("-"))}:${encodeURIComponent(PASS)}@${GATEWAY}`,
  );
}

// A session token keeps the whole app flow — token fetch, list, detail — on one IP.
// An app that changes network address between two calls looks like a hijacked session.
const session = Math.random().toString(16).slice(2, 8);
const dispatcher = agent({ country: "us", session, minutes: 15 });

async function get(url) {
  const res = await fetch(url, { dispatcher, headers: ANDROID });
  const type = res.headers.get("content-type") || "";
  return {
    status: res.status,
    body: type.includes("json") ? await res.json() : (await res.text()).slice(0, 300),
  };
}

const exit = await get("https://ipinfo.io/json");
console.log(`session ${session}`);
console.log(`exit    ${exit.body.ip} (${exit.body.org})`);

const headers = await get("https://httpbin.org/headers");
console.log("\nwhat the server sees:");
for (const [name, value] of Object.entries(headers.body?.headers ?? {})) {
  console.log(`  ${name}: ${String(value).slice(0, 80)}`);
}

console.log(
  "\nThe user-agent, sec-ch-ua-mobile and the carrier ASN all say 'Android phone'. " +
    "That coherence is what the exit IP alone cannot give you.",
);
