# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in this project, please report it **privately**.
Do **not** open a public issue, pull request, or discussion for security matters.

- Preferred: use GitHub's **[Private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)**
  (Security tab → "Report a vulnerability").
- Include a clear description, reproduction steps, affected component(s), and any potential
  impact. If you have a suggested fix, that's welcome too.

Please give a reasonable amount of time for the issue to be addressed before any public
disclosure. We will acknowledge your report, investigate, and keep you informed of progress.

## Scope

This platform runs in an isolated Kubernetes namespace (`easymaid`) and must never affect
any other system. Reports concerning cross-tenant access, secret exposure, authentication or
authorization bypass, payment-flow integrity, or data isolation are especially important.

## Handling of secrets

No secrets are committed to this repository. Configuration secrets (database credentials,
administrator password, Stripe keys, application repository URL) are provided exclusively via
Kubernetes Secrets and site configuration. Only `*.example` templates are tracked in git.

If you believe a secret has been committed, treat it as compromised: report it privately and,
if you have access, rotate the credential immediately.
