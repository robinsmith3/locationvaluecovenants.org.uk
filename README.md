# Location Value Covenants

Source for [locationvaluecovenants.org.uk](https://locationvaluecovenants.org.uk), a static public-policy website published by the Systemic Fiscal Reform Group.

The site explains Location Value Covenants (LVCs): voluntary, property-linked agreements through which a public fund supplies capital, works, services or liability settlement in exchange for a continuing payment linked to local location values.

The material is intended to support public and political discussion. It does not describe a currently available financial product and does not constitute financial, mortgage, pension, tax or legal advice.

## Current release

Release `v1.3.0` contains eight application briefings:

1. Location Value Mortgage
2. Mortgage Rescue
3. Homeowner Pension
4. Paying Inheritance Tax
5. Property Tax Substitution
6. New Home Covenant
7. Wider Property Investment and Support
8. Monetary Stability and Inflation Control

Application cards and their ordering are generated from each page's Markdown front matter.

## Architecture

The project is deliberately small and auditable:

- Markdown source under `content/pages/`
- Shared styles and diagrams under `assets/`
- Static-site generator in `scripts/build.mjs`
- Cloudflare Worker in `src/worker.js`
- Generated site under `public/`
- Automated checks under `tests/`
- Cloudflare configuration in `wrangler.jsonc`

There is no CMS, application database, user-account system, comment system, mailing list or contact form. The site does not deliberately place advertising, behavioural-tracking or first-party analytics cookies. Cloudflare processes the limited network and security information needed to deliver and protect the site, as described in the published Privacy Policy.

## Requirements

- Node.js 20 or later
- npm
- A Cloudflare account with Workers enabled, for maintainers who deploy the site

## Install, build and test

Install the development dependencies:

```bash
npm install
```

Build the static site:

```bash
npm run build
```

Run the build and automated tests:

```bash
npm test
```

The build recreates `public/`. Do not edit files under `public/` manually because the next build will replace them.

## Local development

Run the local Cloudflare development server:

```bash
npm run dev
```

The command builds the site before starting the development server.

## Content maintenance

Ordinary pages are Markdown files under:

```text
content/pages/
```

Application pages are under:

```text
content/pages/applications/
```

Front matter controls the generated page and, for applications, the card shown on the homepage and Applications page. A typical application begins:

```markdown
---
route: /applications/example/
title: Example application
description: A concise search-description for the page.
heading: Example application
intro: A short introduction displayed beneath the page heading.
summary: The text displayed on the application card.
credit: A Systemic Fiscal Reform Group briefing.
number: 09
layout: application
---
```

Application cards are discovered automatically from `layout: application` and ordered by `number`. Do not add card HTML manually to the build script.

Headings can include explicit anchors:

```markdown
## Worked example {#worked-example}
```

The application layout uses explicitly anchored headings to generate its “On this page” navigation.

After changing content, always run:

```bash
npm test
```

## Diagrams and other assets

Website diagrams are stored as SVG files under `assets/`. Editable Mermaid source may be retained alongside an SVG using the `.mmd` extension, but browsers receive the SVG.

When adding a diagram:

1. Add the SVG to `assets/`.
2. Reference it from the relevant Markdown page.
3. Ensure the build copies it into `public/assets/` using the existing asset-handling pattern.
4. Add an automated asset or page assertion where appropriate.
5. Rebuild and inspect it at desktop and mobile widths.

SVGs must include an accessible title and description. Do not include scripts, remote resources, personal information or unpublished notes inside image metadata.

## Deployment

Deployment is restricted to authorised maintainers.

Authenticate Wrangler locally when required:

```bash
npx wrangler login
```

Validate a deployment package without uploading:

```bash
npm run dry-run:staging
npm run dry-run:production
```

Deploy to staging:

```bash
npm run deploy:staging
```

Review the staging site on desktop and mobile, including application navigation, diagrams, the custom 404 page, `robots.txt`, the sitemap and security headers.

Deploy the verified release to production:

```bash
npm run deploy:production
```

Deployment commands run the test suite before uploading.

## Release workflow

A normal release follows this order:

1. Edit source content or code.
2. Run `npm test`.
3. Deploy and inspect staging.
4. Deploy and verify production.
5. Commit and push the verified source.
6. Create an annotated Git tag for a material release.

Example:

```bash
git add --all
git commit -m "Describe the release"
git push origin main
git tag -a v1.4.0 -m "Describe the release"
git push origin v1.4.0
```

Use a new tag for a material, coherent release such as a new application, significant policy revision or structural site change. Small corrections can normally remain ordinary commits until the next release.

## Security

Never commit credentials or private operational material.

In particular, do not commit:

- Cloudflare API tokens
- GitHub tokens
- passwords or email credentials
- private keys or certificates
- `.dev.vars`
- `.env` or environment-specific variants
- Wrangler state or dry-run output
- private correspondence, unpublished source documents or working notes

Deployment credentials must be supplied through local authentication or the repository host's encrypted secret storage. Public identifiers such as a domain name are not credentials, but configuration should still expose only what the project requires.

Before making historical material public, remember that deleting a file in a later commit does not remove it from Git history. Revoke any exposed credential immediately and remove sensitive historical content using an appropriate history-rewriting procedure before publication.

Report security concerns using the contact published at:

```text
https://locationvaluecovenants.org.uk/.well-known/security.txt
```

Do not publish a working exploit or sensitive report in a public issue.

## Contributions and policy discussion

Corrections, evidence and clearly reasoned criticism are welcome. Proposed changes should distinguish between:

- correcting an error;
- clarifying the operation of an existing proposal; and
- advocating a different policy choice.

A merged contribution does not imply endorsement of a political party, candidate, campaign or external organisation. Substantive policy changes remain subject to editorial review by the project maintainers.

## Copyright and reuse

The website source code and the published policy material are distinct works.

Unless otherwise stated, policy text and original diagrams are copyright the Systemic Fiscal Reform Group or the identified author. Reasonable quotation, discussion and non-commercial research use are permitted subject to appropriate attribution and the published [Website Terms of Use](https://locationvaluecovenants.org.uk/website-terms/).

No permission is granted to present altered material as an accurate statement of the project's position. No general open-source licence for the policy text is implied merely because the repository is publicly accessible.

If a separate software licence is added, it applies only to the files and rights expressly identified by that licence.

## Further information

- [Policy briefing](https://locationvaluecovenants.org.uk/briefing/)
- [Applications](https://locationvaluecovenants.org.uk/applications/)
- [Privacy Policy](https://locationvaluecovenants.org.uk/privacy/)
- [Website Terms of Use](https://locationvaluecovenants.org.uk/website-terms/)
