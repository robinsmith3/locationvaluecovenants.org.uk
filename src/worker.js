const LEGACY_REDIRECTS = new Map([
  ["/p/lvc-policy-briefings.html", "/applications/"],
  ["/2025/08/location-value-covenant-lvc-briefing.html", "/briefing/"],
  ["/2023/07/sfr-group-public-policy-links.html", "/briefing/"]
]);

const SITEMAP_PATHS = [
  "/",
  "/briefing/",
  "/applications/",
  "/applications/location-value-mortgage/",
  "/applications/mortgage-rescue/",
  "/applications/homeowner-pension/",
  "/applications/inheritance-tax/",
  "/applications/property-tax/"
];

const SECURITY_HEADERS = {
  "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; upgrade-insecure-requests",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Cross-Origin-Opener-Policy": "same-origin",
  "Cross-Origin-Resource-Policy": "same-origin",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
};

function secure(response, environment) {
  const secured = new Response(response.body, response);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) secured.headers.set(name, value);
  if (environment !== "production") secured.headers.set("X-Robots-Tag", "noindex, nofollow, noarchive");
  return secured;
}

function text(body, contentType, environment, status = 200) {
  return secure(new Response(body, { status, headers: { "Content-Type": contentType } }), environment);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const environment = env.ENVIRONMENT || "staging";

    if (request.method !== "GET" && request.method !== "HEAD") {
      return text("Method Not Allowed\n", "text/plain; charset=utf-8", environment, 405);
    }

    const destination = LEGACY_REDIRECTS.get(url.pathname);
    if (destination) return secure(Response.redirect(new URL(destination, url.origin), 301), environment);

    if (url.pathname === "/robots.txt") {
      const body = environment === "production"
        ? "User-agent: *\nAllow: /\nSitemap: " + url.origin + "/sitemap.xml\n"
        : "User-agent: *\nDisallow: /\n";
      return text(body, "text/plain; charset=utf-8", environment);
    }

    if (url.pathname === "/sitemap.xml") {
      const urls = SITEMAP_PATHS.map((route) => `<url><loc>${url.origin}${route}</loc></url>`).join("");
      return text(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`, "application/xml; charset=utf-8", environment);
    }

    return secure(await env.ASSETS.fetch(request), environment);
  }
};
