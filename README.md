# Location Value Covenants

A framework-free static policy website deployed with Cloudflare Workers Static Assets. It has separate staging and production Workers, no database, no CMS, no analytics and no runtime dependency on Blogger or Google Docs.

## Requirements

- Node.js 20 or later
- A Cloudflare account with Workers enabled
- Wrangler authenticated with `npx wrangler login`

## Install and verify

```bash
npm install
npm test
```

The build produces static HTML in `public/`. The Worker adds security headers, environment-specific crawler controls, the sitemap, `robots.txt`, custom 404 handling and redirects from the retained Blogger URLs.

## Local development

```bash
npm run dev
```

## Deploy staging

```bash
npm run deploy:staging
```

This deploys `location-value-covenants-staging` to its `workers.dev` address and sends `X-Robots-Tag: noindex, nofollow, noarchive` on every response. Its `robots.txt` disallows crawling.

## Deploy production

Review staging first, then run:

```bash
npm run deploy:production
```

This deploys `location-value-covenants-production`. Keep the `workers.dev` URL until the site has been approved. Add the final custom domain in Cloudflare afterwards rather than putting an unconfirmed route in `wrangler.jsonc`.

## Dry-run deployment packages

```bash
npm run dry-run:staging
npm run dry-run:production
```

These commands validate and bundle without uploading anything.

## Content maintenance

Each page is an ordinary Markdown file under `content/pages/`. Shared presentation is in `assets/styles.css`; the page renderer is `scripts/build.mjs`. Edit the relevant Markdown file, then run `npm test`. Do not edit generated files under `public/` directly because every build replaces them.

The front matter at the top of each Markdown file controls its URL, browser title, description, heading and layout. Application pages also have their card summary, credit and display number there.

## Deployment order

1. `npm install`
2. `npm test`
3. `npm run deploy:staging`
4. Review every staging page on desktop and mobile.
5. `npm run deploy:production`
6. Add and verify the custom production domain in Cloudflare.
7. Retire or redirect the Blogger property only after the production domain is confirmed.
