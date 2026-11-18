import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import path from "node:path";
import worker from "../src/worker.js";

const routes = [
  ["public/index.html", "A voluntary route to housing and tax reform"],
  ["public/briefing/index.html", "Location Value Covenants"],
  ["public/applications/index.html", "From principle to practice"],
  ["public/applications/location-value-mortgage/index.html", "Location Value Mortgage"],
  ["public/applications/mortgage-rescue/index.html", "Location Value Mortgage Rescue"],
  ["public/applications/homeowner-pension/index.html", "Homeowner Pension &amp; Equity Release"],
  ["public/applications/inheritance-tax/index.html", "Paying Inheritance Tax"],
  ["public/applications/property-tax/index.html", "Property Tax Substitution"],
  ["public/applications/monetary-stability/index.html", "Monetary Stability &amp; Inflation Control"],
  ["public/privacy/index.html", "Privacy Policy"],
  ["public/website-terms/index.html", "Website Terms of Use"]
];

test("all static routes build with expected content", async () => {
  for (const [file, marker] of routes) {
    const html = await readFile(path.resolve(file), "utf8");
    assert.match(html, /<!doctype html>/i, file);
    assert.ok(html.includes(marker), `${file} is missing ${marker}`);
  }
});

test("excluded Blogger content is absent", async () => {
  const all = (await Promise.all(routes.map(([file]) => readFile(path.resolve(file), "utf8")))).join("\n");
  assert.doesNotMatch(all, /LVC Tokenisation|Requests For Comments|forbidden knowledge/i);
  assert.doesNotMatch(all, /Land Value Covenant/i);
});

test("site has custom 404, robots and sitemap support", async () => {
  const notFound = await readFile(path.resolve("public/404.html"), "utf8");
  assert.match(notFound, /Page not found/);
  const security = await readFile(path.resolve("public/.well-known/security.txt"), "utf8");
  assert.match(security, /Canonical: https:\/\/locationvaluecovenants\.org\.uk\/\.well-known\/security\.txt/);
  assert.match(security, /Expires: 2027-08-20T23:59:59Z/);

  const env = { ENVIRONMENT: "production", ASSETS: { fetch: async () => new Response("asset") } };
  const robots = await worker.fetch(new Request("https://example.com/robots.txt"), env);
  assert.match(await robots.text(), /Allow: \//);
  const sitemap = await worker.fetch(new Request("https://example.com/sitemap.xml"), env);
  assert.match(await sitemap.text(), /<loc>https:\/\/example\.com\/briefing\/<\/loc>/);
});

test("staging is noindex and production receives security headers", async () => {
  const asset = { fetch: async () => new Response("asset", { headers: { "Content-Type": "text/html" } }) };
  const staging = await worker.fetch(new Request("https://staging.example/"), { ENVIRONMENT: "staging", ASSETS: asset });
  assert.equal(staging.headers.get("X-Robots-Tag"), "noindex, nofollow, noarchive");
  assert.match(staging.headers.get("Content-Security-Policy"), /frame-ancestors 'none'/);

  const production = await worker.fetch(new Request("https://example.com/"), { ENVIRONMENT: "production", ASSETS: asset });
  assert.equal(production.headers.get("X-Robots-Tag"), null);
  assert.equal(production.headers.get("X-Content-Type-Options"), "nosniff");
});

test("legacy Blogger pages redirect permanently", async () => {
  const response = await worker.fetch(new Request("https://example.com/p/lvc-policy-briefings.html"), { ENVIRONMENT: "production", ASSETS: { fetch: async () => new Response() } });
  assert.equal(response.status, 301);
  assert.equal(response.headers.get("Location"), "https://example.com/applications/");
});

test("callout blocks render as styled notices, not escaped HTML", async () => {
  for (const file of ["public/index.html", "public/briefing/index.html"]) {
    const html = await readFile(path.resolve(file), "utf8");
    assert.match(html, /<div class="notice"><b>Tax-replacement rule<\/b>/, file);
    assert.doesNotMatch(html, /&lt;div|&lt;p&gt;|:::/, file);
  }
});
