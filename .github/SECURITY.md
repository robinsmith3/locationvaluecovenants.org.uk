# Security Policy

## Reporting a vulnerability

Please report suspected security vulnerabilities privately using the contact published at:

```text
https://locationvaluecovenants.org.uk/.well-known/security.txt
```

Do not disclose a suspected vulnerability in a public GitHub issue, pull request, discussion, social-media post or other public forum before it has been investigated and, where necessary, corrected.

Your report should include, where available:

- A clear description of the issue;
- The affected URL, file, component or Git commit;
- Steps required to reproduce it;
- The security effect you believe it could have;
- Any relevant request and response details, with credentials and personal information removed;
- Whether you believe the issue is already being exploited; and
- A safe way to contact you for clarification.

Please do not send passwords, access tokens, private keys, personal information belonging to another person or data obtained through unnecessary access.

## What this policy covers

This policy covers security issues in:

- The source code in this repository;
- The build and deployment configuration maintained in this repository;
- The Cloudflare Worker code maintained by this project; and
- The production website at `locationvaluecovenants.org.uk` where the issue is caused by project-controlled code or configuration.

Only the latest production release and the current default branch are supported. Historical tags remain available for transparency but do not receive security fixes.

## What is outside scope

The following are outside the scope of this policy:

- Disagreement with, criticism of or errors in the published policy proposals;
- Vulnerabilities in Cloudflare, GitHub, npm or another third-party service that are not caused by this project's configuration or code;
- Findings that require physical access to another person's device;
- Social engineering, phishing or attempts to obtain credentials from maintainers;
- Denial-of-service testing, traffic flooding or activity that could impair availability;
- Automated scanning that generates excessive traffic or alerts;
- Reports based only on missing optional headers or generic scanner output without a credible security effect;
- Public information intentionally included in the repository or website; and
- Hypothetical issues that cannot be reproduced and have no plausible security consequence.

Vulnerabilities in third-party products should be reported to the organisation responsible for that product. If a third-party vulnerability also creates a specific exposure in this project, report the project-specific effect privately.

## Responsible testing

Security research must be proportionate and designed to avoid harm. In particular:

- Use the minimum testing necessary to demonstrate the issue.
- Do not access, alter, retain or disclose information belonging to another person.
- Do not attempt to obtain or use deployment credentials.
- Do not establish persistence or move beyond the affected component.
- Do not degrade the website, evade rate limits or test denial-of-service conditions.
- Do not upload malware or send malicious links to maintainers or visitors.
- Stop testing and report the issue if you encounter non-public information or evidence of active compromise.
- Preserve enough evidence to explain the issue, but do not retain unnecessary sensitive material.

Testing must comply with applicable law. This policy does not authorise access to third-party systems or activities that would otherwise be unlawful.

## Handling reports

Reports will be reviewed and prioritised according to their reproducibility, likely effect and urgency. The project may ask for additional information where necessary to confirm or correct an issue.

Where a vulnerability is confirmed, the project may:

1. Restrict or disable the affected functionality;
2. Correct the source or configuration;
3. Revoke and replace exposed credentials;
4. Deploy and verify the correction;
5. Add an automated regression test; and
6. Publish an appropriate release or advisory after the immediate risk has been addressed.

The reporter will be asked to allow a reasonable period for investigation and correction before any public disclosure. Disclosure timing should reflect the severity of the issue, the availability of a safe correction and any risk to users or infrastructure.

## No bug bounty

The project does not currently operate a paid bug-bounty programme and cannot promise payment, reward or public acknowledgement for reports.

## Repository secrets

No credential should be committed to this repository. If you discover a token, password, private key or other apparent secret in the current tree or Git history:

- Do not attempt to use it;
- Report its location privately and promptly; and
- Do not reproduce the secret in a public issue or report.

An exposed credential will be treated as compromised even if it appears old or inactive.
