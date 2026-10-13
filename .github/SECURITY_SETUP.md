# GitHub Security Setup — Manual Steps

> **For Arif (F13 SOVEREIGN).** This repo is upgraded as of 2026-10-13
> with OpenSSF Scorecards and Dependency Review action. Two security
> surfaces cannot be added via git and need to be enabled via the
> GitHub UI once.

---

## 1. CodeQL Default Setup (UI-only)

CodeQL default setup is GitHub-managed and cannot be committed via git.
Enable it once in repo settings:

1. Navigate to <https://github.com/ariffazil/GEOX/settings/security_analysis>
2. Under "Code security" → "CodeQL analysis" → click **Set up** → **Default**
3. Languages: Python + Actions (both supported in GEOX)
4. Query suite: **Security-and-quality** (default)
5. Click **Enable CodeQL**

GitHub will auto-create a workflow named
`.github/workflows/codeql.yml` (managed, not editable from the repo) and
run the first scan within minutes. After that, weekly scans + every push
to main.

If you want **custom** setup instead of default (more granular control over
queries, paths, languages, builds), the docs reference is:
<https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/configuring-code-scanning-for-a-repository>

---

## 2. Workflow Dependency Lockfile (UI-only)

The "strongest protection" per
[GitHub Docs](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions):
record the exact commit SHA for every action used in `.github/workflows/`,
and reject any workflow run if the SHA in the lockfile doesn't match what
the workflow references.

The lockfile generation is currently a **UI-only action** — there is no
`gh-actions-lockfile` CLI extension as of 2026-Q3 (verified: GitHub CLI
2.100.0 does not ship it; no public OSS extension found).

To enable:

1. Navigate to <https://github.com/ariffazil/GEOX/settings/security_analysis>
2. Wait — there is currently **no first-class UI toggle** for the
   lockfile. The feature is in preview / behind a flag for some accounts.
3. As a **stopgap until UI exposure**: SHA-pin the constitutional-scope
   actions (sentinel, surface-drift-gate, dependabot-ci) by replacing
   `@v7` with `@<full-SHA> # v7.0.x` in their `uses:` lines. Dependabot
   will regenerate matching SHA pins in lockfile-aware workflows once
   enabled.

For now, the workflow files in this repo use SHA-pinned actions (see
`.github/workflows/scorecards.yml` and `.github/workflows/dependency-review.yml`).
Other workflows still use major-version tags. A follow-up PR can
SHA-pin the rest when the lockfile feature is GA.

---

## 3. OpenSSF Scorecard Badge (Optional)

After the first successful Scorecards run, add this badge to README.md
under the existing status block:

```markdown
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/ariffazil/GEOX/badge)](https://scorecard.dev/viewer/?uri=github.com/ariffazil/GEOX)
```

This is the only "bragging rights" surface in the whole upgrade. Skip if
not relevant.

---

## Reference

- [GitHub Docs — Security hardening for GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
- [GitHub Docs — Configuring default setup for code scanning](https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/configuring-default-setup-for-code-scanning)
- [ossf/scorecard-action README](https://github.com/ossf/scorecard-action)
- [actions/dependency-review-action README](https://github.com/actions/dependency-review-action)

---

*Forged 2026-10-13 · Lane 333d · Tier 1 Security Baseline · FI-008 (kimi-code)*
*DITEMPA BUKAN DIBEI — Forged, Not Given.*