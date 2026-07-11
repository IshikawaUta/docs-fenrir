# docs-fenrir

Single-file Fenrir 4.1.2 app (`app.py`) serving Markdown docs from `content/`.

## Commands

```bash
pip install -r requirements.txt
fenrir run app:app --port 8000 --dev    # dev server with auto-reload
python -m pytest tests/ -v              # all tests (unit + e2e, 87 total)
python -m pytest tests/test_app.py -v   # unit only (coverage: 94% app.py)
python -m pytest tests/test_e2e.py -v   # e2e only (46 tests)
```

`pytest.ini` sets `asyncio_mode = auto` — no `@pytest.mark.asyncio` needed.

## Adding a doc page

1. Create `content/<id>.md`
2. Add `{"title": ..., "id": ..., "icon": ..., "description": ...}` to `SIDEBAR` list in `app.py` (~line 77)
3. Search index rebuilds automatically at import time (`_build_search_index()`)

Both `test_all_content_files_exist_in_sidebar` and `test_all_content_files_in_sidebar` verify sidebar ↔ content file parity — they will fail if you forget either side.

## Architecture notes

- **Entrypoint**: `app:app` (Fenrir ASGI app). Also runs via `python app.py`.
- **Markdown rendering**: LRU-cached (128 entries, keyed by filename + mtime). `@lru_cache` on `_cached_render`. Cleared on server restart only.
- **Search**: Pre-built index in memory at module import. All 43 content files indexed. API at `/api/search?q=...`.
- **Static files**: `send_from_directory(STATIC_DIR, path)` with `Cache-Control: public, max-age=86400`.
- **SEO endpoints**: `/sitemap.xml`, `/robots.txt`, `/llms.txt` — all rendered via Jinja2 templates.
- **Sidebar navigation**: 43 entries, no nested groups. Prev/next derived from list index.
- **Monitoring dashboard**: Optional, wrapped in try/except. `.env` credentials ignored by git.

## Vercel deployment

- `api/index.py` imports `app` from `app.py` — Vercel Python runtime auto-detects ASGI.
- `vercel.json`: static files served directly, everything else via serverless function.
- `content/` is included via `includeFiles` in function config.
- Deploy via GitHub Actions: `.github/workflows/deploy.yml` — push to main triggers `vercel deploy --prod`. Requires `VERCEL_TOKEN` secret.

## CI

`.github/workflows/ci.yml` runs pytest on Python 3.10–3.13 for every push/PR to `main`.

## Constraints

- `.env` is gitignored, contains real monitoring credentials — never commit.
- `orjson` is optional; search falls back to stdlib `json.dumps` via `JSONResponse` if not available.
