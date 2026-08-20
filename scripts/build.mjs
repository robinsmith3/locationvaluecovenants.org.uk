import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import site from "./site-source.mjs";

const outputRoot = path.resolve("public");
const origin = "https://location-value-covenants.invalid";
const routes = [
  "/",
  "/briefing/",
  "/applications/",
  "/applications/location-value-mortgage/",
  "/applications/mortgage-rescue/",
  "/applications/homeowner-pension/",
  "/applications/inheritance-tax/",
  "/applications/property-tax/"
];

await rm(outputRoot, { recursive: true, force: true });
await mkdir(outputRoot, { recursive: true });

for (const route of routes) {
  const response = await site.fetch(new Request(`${origin}${route}`));
  if (response.status !== 200) throw new Error(`Build failed for ${route}: HTTP ${response.status}`);
  const directory = route === "/" ? outputRoot : path.join(outputRoot, route);
  await mkdir(directory, { recursive: true });
  await writeFile(path.join(directory, "index.html"), await response.text(), "utf8");
}

const notFound = await site.fetch(new Request(`${origin}/page-not-found/`));
await writeFile(path.join(outputRoot, "404.html"), await notFound.text(), "utf8");

console.log(`Built ${routes.length} pages and 404.html`);
