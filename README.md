# docs-fenrir

Documentation portal for the [Fenrir](https://github.com/IshikawaUta/fenrir) Python web framework v4.1.2. Built with Fenrir itself — a single ASGI application that serves 43 Markdown documentation pages with full-text search, SEO endpoints, and a responsive sidebar layout.

## Features

- **43 documentation pages** covering all Fenrir framework features
- **Full-text search** across all pages via `/api/search?q=...`
- **SEO endpoints**: `/sitemap.xml`, `/robots.txt`, `/llms.txt`
- **Responsive layout** with sidebar navigation, TOC, prev/next pagination
- **LRU-cached Markdown rendering** (128 entries) with syntax highlighting
- **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- **Middleware**: CORS, GZip compression, RequestID, BodyLimit
- **Monitoring dashboard** (optional, via Fenrir built-in monitoring)
- **Deploy-ready for Vercel** with serverless ASGI support

## Quick Start

```bash
pip install -r requirements.txt
fenrir run app:app --port 8000 --dev
```

Open http://localhost:8000. Add `FENRIR_DEV=1` to enable debug pages.

## Project Structure

```
.
├── api/
│   └── index.py              # Vercel serverless entrypoint
├── content/
│   └── *.md                  # 43 Markdown documentation files
├── static/
│   ├── css/
│   ├── images/
│   └── js/
├── templates/
│   ├── index.html
│   ├── layout.html
│   ├── sitemap.xml
│   └── llms.txt
├── tests/
│   ├── test_app.py           # Unit tests (41 tests, 94% coverage)
│   └── test_e2e.py           # E2E tests (46 tests)
├── .env                      # Monitoring credentials (gitignored)
├── .gitignore
├── AGENTS.md
├── app.py                    # Single-file Fenrir application (406 lines)
├── pytest.ini
├── requirements.txt
└── vercel.json
```

## Routes

| Route | Description |
|-------|-------------|
| `/` | Homepage (redirects to `/docs/introduction`) |
| `/docs/<id>` | Documentation page |
| `/api/search?q=...` | Full-text search (JSON) |
| `/static/*` | Static assets (CSS, JS, images) |
| `/sitemap.xml` | XML sitemap |
| `/robots.txt` | Robots exclusion |
| `/llms.txt` | LLM-friendly documentation index |

## Testing

```bash
# All tests
python -m pytest tests/ -v

# Unit tests only
python -m pytest tests/test_app.py -v

# E2E tests only
python -m pytest tests/test_e2e.py -v
```

87 tests total (41 unit + 46 E2E). Unit coverage: 94% of `app.py`.

## Deployment

### Vercel

```bash
npm i -g vercel
vercel login
vercel --prod
```

Or push to `main` — GitHub Actions deploys automatically (requires `VERCEL_TOKEN` secret).

### Manual

```bash
python app.py
```

## Adding a Page

1. Create `content/<id>.md`
2. Add a `SIDEBAR` entry in `app.py` (around line 77)
3. Tests verify sidebar ↔ content file parity — run `pytest` to confirm

## Built With

- [Fenrir](https://github.com/IshikawaUta/fenrir) v4.1.2 — Python web framework
- [Asteri](https://github.com/IshikawaUta/asteri) — ASGI server
- [Jinja2](https://palletsprojects.com/p/jinja/) — HTML templating
- [Markdown](https://python-markdown.github.io/) — with code highlighting, tables, and TOC extensions
- [orjson](https://github.com/ijl/orjson) — fast JSON serialization (optional)
- [Lucide](https://lucide.dev/) — sidebar icons
- [Tailwind CSS](https://tailwindcss.com/) — utility-first styling

## License [MIT](LICENSE)