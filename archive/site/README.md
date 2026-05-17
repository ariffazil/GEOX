# GEOX Site

**Earth Intelligence Skills Catalog + Wiki**

Static site combining ASM-style skill catalog with Karpathy-style minimal wiki.

## Structure

```
geox-site/
├── index.html          # Landing page
├── catalog.html        # ASM-style searchable skills catalog
├── wiki.html           # Karpathy-style doctrine wiki
├── styles.css          # Minimal, fast CSS (no frameworks)
├── app.js              # Client-side search & filter
├── registry.json       # 44 skills across 11 domains
├── skills/             # Individual skill detail pages
│   ├── flood_model.html
│   ├── constitutional_gate.html
│   └── ... (44 total)
└── scripts/
    └── generate_skills.py  # Regenerate skill pages from registry
```

## Deploy

### Option 1: GitHub Pages

1. Push to GitHub repo
2. Enable Pages in repo settings
3. Point to root or `/docs` folder

### Option 2: Cloudflare Pages

```bash
# From geox-site directory
npx wrangler pages deploy . --project-name=geox-skills
```

### Option 3: VPS (Nginx)

```bash
# Copy to web root
sudo cp -r /root/geox-site/* /var/www/geox-skills/

# Nginx config
server {
    listen 80;
    server_name skills.geox.arif-fazil.com;
    root /var/www/geox-skills;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
}
```

## Domain Options

- `geox.arif-fazil.com` — Main landing
- `skills.geox.arif-fazil.com` — This catalog
- `wiki.geox.arif-fazil.com` — Wiki-only mirror

## Regenerate Skill Pages

```bash
cd /root/geox-site
python3 scripts/generate_skills.py
```

## Features

- **Search**: Client-side filtering by text, domain, substrate
- **No frameworks**: Pure HTML/CSS/JS, ~10KB CSS, ~6KB JS
- **MCP ready**: Each skill exposes `geox://resources/{domain}/{skill}` URI
- **Mobile responsive**: Works on all screen sizes
- **Fast**: No build step, instant page loads

## Seal

> DITEMPA BUKAN DIBERI — Forged, Not Given

ΔΩΨ — SOUL · MIND · VOID
