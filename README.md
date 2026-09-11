# docs-fenrir

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Fenrir-4.4.0-9b59b6.svg)](https://pypi.org/project/fenrir-framework/)
[![Tests](https://img.shields.io/badge/Tests-100%20Passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/Coverage-100%25-green.svg)]()
[![CI](https://github.com/IshikawaUta/docs-fenrir/actions/workflows/ci.yml/badge.svg)](https://github.com/IshikawaUta/docs-fenrir/actions/workflows/ci.yml)
[![Deployment](https://img.shields.io/badge/Deployed-Vercel-black.svg)](https://vercel.app)
[![Code Quality](https://img.shields.io/badge/Ruff-Passed-00b841.svg)]()
[![Type Check](https://img.shields.io/badge/Mypy-Passed-9b59b6.svg)]()

Documentation portal for the [Fenrir](https://github.com/IshikawaUta/fenrir) Python web framework v4.4.0. Built with Fenrir itself — a single ASGI application that serves 43 Markdown documentation pages with full-text search, SEO endpoints, interactive playground, and a responsive sidebar layout.

## Features

- **43 documentation pages** covering all Fenrir framework features
- **Interactive playground** — run Fenrir code directly in your browser (Pyodide/WebAssembly)
- **Full-text search** across all pages via `/api/search?q=...`
- **SEO endpoints**: `/sitemap.xml`, `/robots.txt`, `/llms.txt`
- **Responsive layout** with sidebar navigation, TOC, prev/next pagination
- **Dark mode** — automatic detection with manual toggle
- **LRU-cached Markdown rendering** (128 entries) with syntax highlighting
- **Security headers**: HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, Cross-Origin-Opener-Policy, XSS Protection
- **Rate limiting**: 1000 requests per 60 seconds
- **Middleware**: CORS, GZip compression, RequestID, BodyLimit, SecurityHeaders
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support
- **API Documentation**: OpenAPI 3.0 spec + Swagger UI + ReDoc
- **Error monitoring**: Sentry integration (optional)
- **Health check**: `/health` endpoint for uptime monitoring
- **Performance**: Core Web Vitals monitoring, font preloading, CSS containment
- **Deploy-ready for Vercel** with serverless ASGI support

## Quick Start

```bash
# Clone repository
git clone https://github.com/IshikawaUta/docs-fenrir.git
cd docs-fenrir

# Install dependencies
pip install -r requirements.txt

# Run development server
fenrir run app:app --port 8000 --dev
```

Open http://localhost:8000. Add `FENRIR_DEV=1` to enable debug pages.

## Project Structure

```
.
├── api/
│   └── index.py                  # Vercel serverless entrypoint
├── content/
│   └── *.md                      # 43 Markdown documentation files
├── static/
│   ├── css/
│   │   └── style.css             # Main stylesheet (dark mode, responsive)
│   ├── images/
│   │   ├── favicon.png           # Site favicon
│   │   └── logo.jpg              # Fenrir logo
│   └── js/
│       └── main.js               # Keyboard nav, search, accessibility
├── templates/
│   ├── index.html                # Homepage template
│   ├── layout.html               # Base layout (sidebar, TOC, header)
│   ├── playground.html           # Interactive code playground
│   ├── sitemap.xml               # XML sitemap template
│   └── llms.txt                  # LLM-friendly documentation index
├── tests/
│   ├── test_app.py               # Unit tests (54 tests)
│   └── test_e2e.py               # E2E tests (46 tests)
├── .coveragerc                   # Coverage configuration
├── .env                          # Environment variables (gitignored)
├── .env.example                  # Environment variables template
├── .github/
│   └── workflows/
│       ├── ci.yml                # CI: ruff + mypy + pytest
│       └── deploy.yml            # CD: Vercel deployment
├── app.py                        # Single-file Fenrir application (634 lines)
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
└── vercel.json                   # Vercel deployment config
```

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Homepage (redirects to `/docs/introduction`) |
| `/playground` | GET | Interactive Python playground (Pyodide) |
| `/docs/<id>` | GET | Documentation page |
| `/api/search?q=...` | GET | Full-text search (JSON) |
| `/api/openapi.json` | GET | OpenAPI 3.0 specification |
| `/docs/swagger` | GET | Swagger UI |
| `/docs/redoc` | GET | ReDoc |
| `/health` | GET | Health check endpoint |
| `/sitemap.xml` | GET | XML sitemap |
| `/robots.txt` | GET | Robots exclusion |
| `/llms.txt` | GET | LLM-friendly documentation index |
| `/static/*` | GET | Static assets (CSS, JS, images) |

## Testing

```bash
# All tests
python -m pytest tests/ -v

# Unit tests only
python -m pytest tests/test_app.py -v

# E2E tests only
python -m pytest tests/test_e2e.py -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Type checking
mypy app.py tests

# Linting
ruff check .
```

100 tests total (54 unit + 46 E2E). Coverage: 100% of `app.py`.

## Code Quality

```bash
# Run all checks
ruff check . && mypy app.py tests && python -m pytest tests/ -q
```

CI runs automatically on push/PR to `main`:
1. **Ruff** — import sorting, type hints, code style
2. **Mypy** — static type checking
3. **Pytest** — unit + E2E tests

## Deployment

### Vercel (Recommended)

```bash
npm i -g vercel@39.2.8
vercel login
vercel --prod
```

Or push to `main` — GitHub Actions deploys automatically (requires `VERCEL_TOKEN` secret).

### Manual

```bash
python app.py
```

### Docker

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["fenrir", "run", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FENRIR_DEV` | Enable dev mode | No | `0` |
| `SENTRY_DSN` | Sentry error monitoring DSN | No | - |
| `ENVIRONMENT` | App environment | No | `production` |
| `MONITORING_ENABLED` | Enable monitoring dashboard | No | `false` |
| `MONITORING_USER` | Monitoring dashboard username | No | - |
| `MONITORING_PASSWORD` | Monitoring dashboard password | No | - |
| `MONITORING_SITES` | Comma-separated sites to monitor | No | `http://localhost:8000` |
| `VERCEL_TOKEN` | Vercel deployment token (CI only) | Yes (CI) | - |

## Security

- **Security headers**: HSTS, X-Frame-Options (DENY), X-Content-Type-Options (nosniff), Referrer-Policy, Permissions-Policy, Cross-Origin-Opener-Policy
- **Rate limiting**: 1000 requests per 60 seconds per IP
- **Body size limit**: 1MB max request body
- **CORS**: Configurable allowed origins
- **GZip compression**: Responses > 500 bytes
- **Sentry integration**: Optional error monitoring with PII scrubbing
- **Vercel headers**: Additional security headers as defense-in-depth

## Adding a Page

1. Create `content/<id>.md` with frontmatter:
   ```markdown
   ---
   title: Page Title (50-60 chars for SEO)
   description: Page description (120-150 chars for SEO)
   ---
   
   # Page Content
   ```

2. Add a SIDEBAR entry in `app.py`:
   ```python
   {"title": "Page Title", "id": "<id>", "icon": "icon-name", "description": "SEO description"}
   ```

3. Run tests to verify sidebar ↔ content file parity:
   ```bash
   pytest tests/ -q
   ```

## Documentation Pages

| Section | Pages |
|---------|-------|
| **Getting Started** | Introduction, Installation, Project Structure, Quick Start, Basic Concepts |
| **Core Features** | Routing, Request & Response, Dependency Injection, Data Validation, Context Locals, Class-Based Resources |
| **Advanced** | File Upload, WebSocket, Server-Sent Events, Templating, Error Handling, Middleware, Sessions, Pagination, Background Tasks, Authentication |
| **Architecture** | Blueprints, Configuration, Testing, CLI Tools, Advanced Features |
| **v4.4.0 New** | Plugin System, Hook System, ORM, Caching, Queue System, GraphQL, gRPC, Performance, Monitoring, Signals, JSON Provider, OpenAPI |
| **Reference** | Best Practices, Comparison, Conclusion |

## Built With

- [Fenrir](https://github.com/IshikawaUta/fenrir) v4.4.0 — Python web framework
- [Asteri](https://github.com/IshikawaUta/asteri) — ASGI server
- [Jinja2](https://palletsprojects.com/p/jinja/) — HTML templating
- [Markdown](https://python-markdown.github.io/) — with code highlighting, tables, and TOC extensions
- [Pydantic](https://docs.pydantic.dev/) — data validation
- [orjson](https://github.com/ijl/orjson) — fast JSON serialization
- [Sentry](https://sentry.io/) — error monitoring
- [Pyodide](https://pyodide.org/) — Python in browser (playground)
- [Lucide](https://lucide.dev/) — sidebar icons
- [Tailwind CSS](https://tailwindcss.com/) — utility-first styling

## Performance

- **LRU cache**: 128-entry markdown cache with mtime invalidation
- **Precompiled regex**: Patterns compiled once, reused on every request
- **Font preloading**: Inter + JetBrains Mono with `font-display: swap`
- **CSS containment**: `contain: layout style paint` for isolated rendering
- **Core Web Vitals**: LCP, FID, CLS, TTFB monitoring via PerformanceObserver
- **Reduced motion**: Respects `prefers-reduced-motion` media query

## License

[MIT](LICENSE)
