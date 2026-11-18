import { readFile, readdir, rm, mkdir, writeFile, copyFile } from "node:fs/promises";

const CONTENT = new URL("../content/pages/", import.meta.url);
const PUBLIC = new URL("../public/", import.meta.url);
const NAME = "Location Value Covenants";
const escapeHtml = value => value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const slug = value => value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");

function inline(value) {
  return escapeHtml(value)
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" loading="lazy">')
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
}

function markdown(source) {
  const lines = source.trim().split(/\r?\n/), html = [];
  for (let i = 0; i < lines.length;) {
    const line = lines[i].trim();
    if (!line) { i++; continue; }
    const notice = /^:::notice\s+(.+)$/.exec(line);
    if (notice) {
      const body = []; i++;
      while (i < lines.length && lines[i].trim() !== ":::") body.push(lines[i++]);
      i++;
      html.push(`<div class="notice"><b>${inline(notice[1])}</b>${markdown(body.join("\n"))}</div>`); continue;
    }
    const heading = /^(#{2,4})\s+(.+?)(?:\s+\{#([^}]+)\})?$/.exec(line);
    if (heading) { const level = heading[1].length; html.push(`<h${level} id="${heading[3] || slug(heading[2])}">${inline(heading[2])}</h${level}>`); i++; continue; }
    if (line.startsWith("|")) {
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) rows.push(lines[i++].trim().slice(1, -1).split("|").map(x => x.trim()));
      const data = rows.filter((_, index) => index !== 1), head = data.shift();
      html.push(`<div class="table" tabindex="0" role="region" aria-label="Data table"><table><thead><tr>${head.map(x => `<th>${inline(x)}</th>`).join("")}</tr></thead><tbody>${data.map(row => `<tr>${row.map((x, index) => index ? `<td>${inline(x)}</td>` : `<th>${inline(x)}</th>`).join("")}</tr>`).join("")}</tbody></table></div>`); continue;
    }
    if (/^[-*]\s+/.test(line)) { const items = []; while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) items.push(lines[i++].trim().replace(/^[-*]\s+/, "")); html.push(`<ul>${items.map(x => `<li>${inline(x)}</li>`).join("")}</ul>`); continue; }
    if (/^\d+\.\s+/.test(line)) { const items = []; while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) items.push(lines[i++].trim().replace(/^\d+\.\s+/, "")); html.push(`<ol>${items.map(x => `<li>${inline(x)}</li>`).join("")}</ol>`); continue; }
    const paragraph = [];
    while (i < lines.length && lines[i].trim() && !/^(#{2,4})\s|^[-*]\s+|^\d+\.\s+|^\||^:::/.test(lines[i].trim())) paragraph.push(lines[i++].trim());
    html.push(`<p>${inline(paragraph.join(" "))}</p>`);
  }
  return html.join("\n");
}

function tableOfContents(source) {
  const links = source
    .trim()
    .split(/\r?\n/)
    .map(line =>
      /^(#{2,4})\s+(.+?)\s+\{#([^}]+)\}\s*$/.exec(line.trim())
    )
    .filter(Boolean)
    .map(match =>
      `<a href="#${escapeHtml(match[3])}">${inline(match[2])}</a>`
    )
    .join("");

  return `<aside class="toc"><b>On this page</b>${links}</aside>`;
}

function applicationTableOfContents(source) {
  const topics = [
    ["basic-concept", "Basic concept"],
    ["worked-example", "Worked example"],
    ["how-it-works", "How the LVC works"],
    ["beneficiaries", "The beneficiaries"],
    ["policy-effect", "Policy effect"]
  ];

  const anchorsPresent = new Set(
    source
      .trim()
      .split(/\r?\n/)
      .map(line =>
        /^(#{2,4})\s+.+?\s+\{#([^}]+)\}\s*$/.exec(line.trim())
      )
      .filter(Boolean)
      .map(match => match[2])
  );

  const links = topics
    .filter(([anchor]) => anchorsPresent.has(anchor))
    .map(([anchor, label]) =>
      `<a href="#${anchor}">${escapeHtml(label)}</a>`
    )
    .join("");

  return `<aside class="toc"><b>On this page</b>${links}</aside>`;
}

function parsePage(source, filename) {
  const match = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/m.exec(source);
  if (!match) throw new Error(`${filename}: missing front matter`);
  const meta = {};
  for (const line of match[1].split("\n")) { const index = line.indexOf(":"); if (index > 0) meta[line.slice(0, index).trim()] = line.slice(index + 1).trim().replace(/^"|"$/g, ""); }
  for (const required of ["route", "title", "description", "heading", "layout"]) if (!meta[required]) throw new Error(`${filename}: missing ${required}`);
  return { meta, body: match[2] };
}

const card = page => `<a href="${page.meta.route}"><small>${page.meta.number}</small><h3>${escapeHtml(page.meta.heading)}</h3><p>${escapeHtml(page.meta.summary)}</p><b>Read briefing →</b></a>`;
const cards = apps => `<div class="cards">${apps.map(card).join("")}</div>`;
const hero = page => `<header class="pagehero"><div class="wrap"><small>${escapeHtml(page.meta.eyebrow || "Policy")}</small><h1>${escapeHtml(page.meta.heading)}</h1><p>${escapeHtml(page.meta.intro || page.meta.description)}</p></div></header>`;

function bodyFor(page, apps) {
  const content = markdown(page.body);
  if (page.meta.layout === "home") return `<section class="wrap homehero"><div><small>${escapeHtml(page.meta.eyebrow)}</small><h1>${escapeHtml(page.meta.heading)}</h1><p class="lead">${escapeHtml(page.meta.intro)}</p><p><a class="button" href="/briefing/">Read the policy briefing</a><a class="button ghost" href="/applications/">Explore ${apps.length} applications</a></p></div><aside><small>The proposition</small><ol><li><b>Voluntary</b><span>Property owners choose whether to participate.</span></li><li><b>Lower risk</b><span>Payments track local rental value rather than interest rates.</span></li><li><b>Public benefit</b><span>Revenue flows to public purposes rather than mortgage interest.</span></li></ol></aside></section><div class="wrap policy-content">${content}<h2>Explore ways the covenant can be used</h2>${cards(apps)}</div>`;
  if (page.meta.layout === "applications") return `${hero(page)}<section class="wrap section">${content}${cards(apps)}<div class="notice"><b>A note on the examples</b><p>Monetary figures and tax references illustrate the mechanism at the time of writing; they are not current quotations, calculations or personal advice.</p></div></section>`;
  if (page.meta.layout === "register") {
    const toc = tableOfContents(page.body);
    return `${hero(page)}<div class="wrap layout">${toc}<article class="policy-content">${content}<div class="notice"><b>Demonstration status</b><p>The published figures are synthetic. They demonstrate the proposed register and must not be treated as actual postcode valuations or financial advice.</p></div><nav class="article-nav"><a href="/briefing/">Policy briefing</a><a href="/applications/">Applications</a></nav></article></div>`;
  }
  if (page.meta.layout === "application") {
    const toc = applicationTableOfContents(page.body);
    return `<header class="apphero"><div class="wrap"><a href="/applications/">← All applications</a><small>Application ${page.meta.number}</small><h1>${escapeHtml(page.meta.heading)}</h1><p>${escapeHtml(page.meta.intro)}</p><i>${escapeHtml(page.meta.credit)}</i></div></header><div class="wrap layout">${toc}<article>${content}<div class="notice"><b>Illustrative figures</b><p>Financial values, rates and tax references restyle the original policy example. They explain the proposed mechanism and are not current financial, tax or legal advice.</p></div><nav class="article-nav"><a href="/applications/">All applications</a><a href="/briefing/">Policy briefing</a></nav></article></div>`;
  }
    const toc = tableOfContents(page.body);

    return `${hero(page)}<div class="wrap layout">${toc}<article class="policy-content">${content}</article></div>`;
}

function header(route) {
  const active =
    route === "/"
      ? "home"
      : route.startsWith("/briefing")
        ? "briefing"
        : route.startsWith("/applications")
          ? "applications"
          : route.startsWith("/model")
            ? "model"
            : route.startsWith("/register") 
              ? "register" 
                : "";

  return `
    <a class="skip" href="#main">Skip to content</a>
    <header class="head">
      <div class="wrap nav">
        <a class="brand" href="/">
          <span class="mark">LVC</span>
          <span>${NAME}</span>
        </a>

        <nav class="links" aria-label="Main navigation">
          <a
            ${active === "home" ? 'aria-current="page"' : ""}
            href="/"
          >Home</a>

          <a
            ${active === "briefing" ? 'aria-current="page"' : ""}
            href="/briefing/"
          >Policy briefing</a>

          <a
            ${active === "applications" ? 'aria-current="page"' : ""}
            href="/applications/"
          >Applications</a>

          <a
            ${active === "model" ? 'aria-current="page"' : ""}
            href="/model/"
          >National model</a>
          <a 
            ${active === "register" ? 'aria-current="page"' : ""} 
            href="/register/"
          >The Register</a>
        </nav>
      </div>
    </header>
  `;
}

function shell(page, apps, css) {
  const footer = `
    <footer class="foot">
      <div class="wrap footgrid">
        <div>
          <b>${NAME}</b>
          <p>
            A voluntary policy proposal for housing finance and
            public revenue reform.
          </p>
          <p>
            Contact:
            <a href="mailto:locationvaluecovenants@gmail.com">
              locationvaluecovenants@gmail.com
            </a>
          </p>
        </div>

        <nav aria-label="Footer navigation">
          <a href="/briefing/">Policy briefing</a>
          <a href="/applications/">Applications</a>
          <a href="/register/">The Register</a><a href="/model/">National model</a>
          <a href="/privacy/">Privacy</a>
          <a href="/website-terms/">Terms</a>
        </nav>
      </div>

      <div class="wrap fine">
        Policy material from the Systemic Fiscal Reform Group ·
        © ${new Date().getUTCFullYear()}
      </div>
    </footer>
  `;

  return `<!doctype html>
<html lang="en-GB">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>${escapeHtml(page.meta.title)} — ${NAME}</title>
  <meta
    name="description"
    content="${escapeHtml(page.meta.description)}"
  >
  <link rel="icon" href="/favicon.ico" sizes="32x32">
  <link
    rel="icon"
    href="/favicon.svg?v=2"
    type="image/svg+xml"
    sizes="any"
  >
  <style>${css}</style>
</head>
<body>
  ${header(page.meta.route)}
  <main id="main">
    ${bodyFor(page, apps)}
  </main>
  ${footer}
</body>
</html>`;
}

async function filesUnder(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) { const target = new URL(entry.name + (entry.isDirectory() ? "/" : ""), directory); if (entry.isDirectory()) files.push(...await filesUnder(target)); else if (entry.name.endsWith(".md")) files.push(target); }
  return files;
}

const css = `${await readFile(new URL("../assets/styles.css", import.meta.url), "utf8")}\n${await readFile(new URL("../assets/content.css", import.meta.url), "utf8")}`, pages = [];
for (const file of await filesUnder(CONTENT)) pages.push(parsePage(await readFile(file, "utf8"), file.pathname));
const apps = pages.filter(page => page.meta.layout === "application").sort((a, b) => a.meta.number.localeCompare(b.meta.number));
await rm(PUBLIC, { recursive: true, force: true }); await mkdir(PUBLIC, { recursive: true });
await mkdir(new URL("assets/", PUBLIC), { recursive: true });
await copyFile(
  new URL("../assets/lvc-in-action.svg", import.meta.url),
  new URL("assets/lvc-in-action.svg", PUBLIC)
);
await copyFile(
  new URL("../assets/monetary-stability-policy-flow.svg", import.meta.url),
  new URL("assets/monetary-stability-policy-flow.svg", PUBLIC)
);
await copyFile(
  new URL("../assets/favicon.ico", import.meta.url),
  new URL("favicon.ico", PUBLIC)
);
await copyFile(
  new URL("../assets/homeowner-pension-in-action.svg", import.meta.url),
  new URL("assets/homeowner-pension-in-action.svg", PUBLIC)
);
await copyFile(
  new URL("../assets/mortgage-rescue-in-action.svg", import.meta.url),
  new URL("assets/mortgage-rescue-in-action.svg", PUBLIC)
);
await copyFile(
  new URL("../assets/inheritance-tax-in-action.svg", import.meta.url),
  new URL("assets/inheritance-tax-in-action.svg", PUBLIC)
);
await copyFile(
  new URL("../assets/property-tax-in-action.svg", import.meta.url),
  new URL("assets/property-tax-in-action.svg", PUBLIC)
);
await copyFile(
  new URL(
    "../assets/wider-property-investment-and-support.svg", import.meta.url),
  new URL("assets/wider-property-investment-and-support.svg", PUBLIC)
);
await copyFile(
  new URL("../assets/new-home-covenant.svg", import.meta.url),
  new URL("assets/new-home-covenant.svg", PUBLIC)
);
await copyFile(
  new URL("../assets/favicon.svg", import.meta.url),
  new URL("favicon.svg", PUBLIC)
);

await copyFile(
  new URL("../assets/favicon.ico", import.meta.url),
  new URL("favicon.ico", PUBLIC)
);

await copyFile(
  new URL("../assets/brownfield-land-covenant.svg", import.meta.url),
  new URL("assets/brownfield-land-covenant.svg", PUBLIC)
);

await copyFile(
  new URL("../assets/empty-homes-covenant.svg", import.meta.url),
  new URL("assets/empty-homes-covenant.svg", PUBLIC)
);

await mkdir(new URL("assets/register/", PUBLIC), { recursive: true });

for (const name of [
  "map-2026.svg",
  "distribution-2026.svg",
  "register-2026.csv",
  "summary-2026.csv",
  "methodology.md",
  "lvc-register.py",
  "postcodes-2026.csv",
  "evidence-2026.csv",
  "make-register-map.py",
  "make-published-rents-demo.py",
  "ons-private-rents-source-2026-08.csv",
  "README.md"
]) {
  await copyFile(
    new URL("../assets/register/" + name, import.meta.url),
    new URL("assets/register/" + name, PUBLIC)
  );
}

await mkdir(new URL("assets/model/", PUBLIC), { recursive: true });

for (const filename of [
  "conservative.svg",
  "average.svg",
  "best-case.svg",
  "feedback-loop.svg",
  "conservative.csv",
  "average.csv",
  "best-case.csv",
  "lvc_national_model.py"
]) {
  await copyFile(
    new URL(`../assets/model/${filename}`, import.meta.url),
    new URL(`assets/model/${filename}`, PUBLIC)
  );
}

await copyFile(
  new URL("../assets/family-farm-covenant.svg", import.meta.url),
  new URL("assets/family-farm-covenant.svg", PUBLIC)
);

await copyFile(
  new URL("../assets/tenant-and-rental-covenant.svg", import.meta.url),
  new URL("assets/tenant-and-rental-covenant.svg", PUBLIC)
);

for (const page of pages) { const relative = page.meta.route === "/" ? "index.html" : `${page.meta.route.slice(1)}index.html`; const destination = new URL(relative, PUBLIC); await mkdir(new URL("./", destination), { recursive: true }); await writeFile(destination, shell(page, apps, css)); }
const notFound = { meta: { route: "/404/", title: "Page not found", description: "The requested page could not be found.", heading: "Page not found", intro: "The page may have moved as part of the new policy-site structure.", eyebrow: "404", layout: "standard" }, body: "[Return to the home page](/)" };
await writeFile(new URL("404.html", PUBLIC), shell(notFound, apps, css));
await mkdir(new URL(".well-known/", PUBLIC), { recursive: true });
await writeFile(new URL(".well-known/security.txt", PUBLIC), "Contact: mailto:locationvaluecovenants@gmail.com\nCanonical: https://locationvaluecovenants.org.uk/.well-known/security.txt\nPreferred-Languages: en\nExpires: 2027-08-20T23:59:59Z\n");
const sitemapRoutes = pages.map(page => page.meta.route).sort((a, b) => (a === "/" ? -1 : b === "/" ? 1 : a.localeCompare(b)));
await writeFile(new URL("../src/sitemap-paths.js", import.meta.url), `// Generated by scripts/build.mjs from content/pages front matter. Do not edit by hand.\nexport const SITEMAP_PATHS = ${JSON.stringify(sitemapRoutes, null, 2)};\n`);
console.log(`Built ${pages.length} pages and 404.html from Markdown`);
