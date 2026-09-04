# Security Policy

## Reporting a Vulnerability

GEOX handles geological data that can be commercially sensitive (exploration prospects,
reservoir properties, well data). Please do NOT open a public issue for security vulnerabilities.

Contact: **arifbfazil@gmail.com**

Include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact on data integrity or confidentiality

We will acknowledge receipt within 48 hours.

## Security Architecture

- All core services bind `127.0.0.1` — firewalled by UFW, not publicly exposed
- Federation communication occurs over private Tailscale mesh (`100.64.0.0/24`)
- No secrets stored in the repository — secrets via `/root/.secrets/kunci-root.env`
- BSL-1.1 license restricts production use without explicit permission

## Data Handling

GEOX processes SEG-Y, LAS, and other proprietary geological data formats.
- User data is never stored permanently unless explicitly configured
- Processing is stateless by default — no residual data after API response
- PaleoDB queries use public endpoints only
