import os
import re
import html
import datetime
import logging
from functools import lru_cache

from fenrir import (
    Fenrir,
    request,
    g,
    render_template,
    JSONResponse,
    Response,
    TextResponse,
    HTTPNotFound,
    CORSMiddleware,
    GZipMiddleware,
    RequestIDMiddleware,
    BodyLimitMiddleware,
    send_from_directory,
)
from fenrir.features import init_fenrir_monitoring

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("docs-fenrir")

app = Fenrir(
    title="Fenrir Docs",
    version="3.1.3",
    dev_mode=os.environ.get("FENRIR_DEV", "0") == "1",
)

# --- Middleware (outermost first) ---
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)
app.add_middleware(BodyLimitMiddleware, max_content_length=1_048_576)  # 1 MB
app.add_middleware(RequestIDMiddleware)

init_fenrir_monitoring(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content")

SIDEBAR = [
    {"title": "Introduction to Fenrir", "id": "introduction", "icon": "info", "description": "Fenrir is a high-performance hybrid Python web framework combining Flask, FastAPI, Falcon, and Sanic paradigms."},
    {"title": "Installation Guide", "id": "installation", "icon": "download", "description": "Learn how to install Fenrir framework and its dependencies step by step."},
    {"title": "Project Structure", "id": "project-structure", "icon": "folder", "description": "Recommended file and directory layout for Fenrir applications."},
    {"title": "Quick Start Guide", "id": "quick-start", "icon": "play", "description": "Build your first Fenrir application with a Hello World walkthrough."},
    {"title": "Basic Concepts", "id": "basic-concepts", "icon": "book-open", "description": "Core framework concepts including app constructor, dev_mode, and configuration."},
    {"title": "Routing System", "id": "routing", "icon": "git-commit", "description": "How Fenrir routing works with path parameters, converters, and regex patterns."},
    {"title": "Request & Response", "id": "request-response", "icon": "arrow-left-right", "description": "Accessing request headers, variables, and building custom responses."},
    {"title": "Dependency Injection", "id": "dependency-injection", "icon": "plug", "description": "FastAPI-style dependency injection with Depends, yield deps, and overrides."},
    {"title": "Data Validation", "id": "data-validation", "icon": "check-circle", "description": "Pydantic model integration for automatic request validation."},
    {"title": "Context Locals", "id": "context-locals", "icon": "database", "description": "Thread-safe context variables: request, session, g, and current_app."},
    {"title": "Class-Based Resources", "id": "class-based-resources", "icon": "layers", "description": "Falcon-style class-based resources with on_get, on_post methods."},
    {"title": "File Upload", "id": "file-upload", "icon": "upload", "description": "Handle standard and multipart file uploads in Fenrir."},
    {"title": "WebSocket Support", "id": "websocket", "icon": "zap", "description": "Build real-time WebSocket endpoints with Fenrir."},
    {"title": "Server-Sent Events (SSE)", "id": "server-sent-events", "icon": "radio", "description": "Stream real-time events to clients using Server-Sent Events."},
    {"title": "Jinja2 Templating", "id": "templating", "icon": "layout", "description": "Render HTML templates with built-in Jinja2 integration."},
    {"title": "Error Handling & Exceptions", "id": "error-handling", "icon": "alert-circle", "description": "Handle HTTP status codes and custom exceptions in Fenrir."},
    {"title": "Error Handling Compatibility", "id": "error-handling-compatibility", "icon": "shuffle", "description": "Multi-style error handling compatibility across frameworks."},
    {"title": "Middleware System", "id": "middleware", "icon": "cpu", "description": "Request and response middleware hooks for Fenrir applications."},
    {"title": "Middleware Classes", "id": "middleware-classes", "icon": "layers", "description": "Built-in ASGI middleware: CORS, GZip, RequestID, RateLimit, BodyLimit, CSRF."},
    {"title": "Sessions", "id": "sessions", "icon": "database", "description": "Session backends: secure cookies, in-memory, and Redis storage."},
    {"title": "Pagination", "id": "pagination", "icon": "list", "description": "Paginated list responses with PaginationParams utility."},
    {"title": "Background Tasks", "id": "background-tasks", "icon": "clock", "description": "Run background workers without blocking request handlers."},
    {"title": "Authentication & Security", "id": "authentication-security", "icon": "shield", "description": "API keys, JWT, Bearer tokens, OAuth2, OpenID Connect, and WebSocket auth."},
    {"title": "Blueprints Organization", "id": "blueprints", "icon": "map", "description": "Modularize routes with Fenrir blueprints."},
    {"title": "Application Configuration", "id": "configuration", "icon": "settings", "description": "Configure Fenrir apps with settings and environment variables."},
    {"title": "Testing Guide", "id": "testing", "icon": "clipboard-list", "description": "Write test cases with pytest and Fenrir's TestClient."},
    {"title": "CLI Tools Reference", "id": "cli-tools", "icon": "terminal", "description": "CLI commands: run, routes, shell, bench, new, info, and monitoring."},
    {"title": "Advanced Features", "id": "advanced-features", "icon": "sliders", "description": "Dev mode, WSGI mounting, connection pooling, and multiple response models."},
    {"title": "Monitoring Dashboard", "id": "monitoring", "icon": "activity", "description": "Built-in monitoring: health checks, traffic analysis, and alerts."},
    {"title": "Signals System", "id": "signals", "icon": "radio", "description": "Event-driven programming with Fenrir signals."},
    {"title": "JSON Provider", "id": "json-provider", "icon": "braces", "description": "Custom JSON serialization with tagged types support."},
    {"title": "OpenAPI Customization", "id": "openapi-customization", "icon": "file-text", "description": "Swagger UI, ReDoc, and OpenAPI route metadata customization."},
    {"title": "Best Practices", "id": "best-practices", "icon": "award", "description": "Recommended patterns for production-ready Fenrir applications."},
    {"title": "Framework Comparison", "id": "comparison", "icon": "bar-chart", "description": "Compare Fenrir vs Flask vs FastAPI vs Sanic vs Falcon vs Bottle."},
    {"title": "Conclusion", "id": "conclusion", "icon": "flag", "description": "Closing notes, full changelog, and Fenrir v3.1.3 release history."},
]

_SIDEBAR_INDEX = {item["id"]: i for i, item in enumerate(SIDEBAR)}

# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension

_MD_EXTENSIONS = [
    "extra",
    FencedCodeExtension(),
    CodeHiliteExtension(css_class="highlight", linenums=True),
    TableExtension(),
    TocExtension(baselevel=1, marker=None),
]

_EXTERNAL_LINK_RE = re.compile(
    r'<a\s+(?![^>]*rel=)([^>]*href="https?://[^"]+"[^>]*)>'
)
_TABLE_RE = re.compile(r'(<table\b.*?</table>)', re.DOTALL)
_STRIP_HTML_RE = re.compile(r'<[^>]+>')


def render_markdown(filename: str):
    filepath = os.path.join(CONTENT_DIR, f"{filename}.md")
    try:
        mtime = os.path.getmtime(filepath)
    except OSError:
        return None, None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    md = markdown.Markdown(extensions=_MD_EXTENSIONS)
    html = md.convert(content)

    html = _EXTERNAL_LINK_RE.sub(
        r'<a \1 rel="noopener noreferrer" target="_blank">', html
    )
    html = _TABLE_RE.sub(r'<div class="table-wrapper">\1</div>', html)

    return html, md.toc


@lru_cache(maxsize=64)
def _cached_render(filename: str, _mtime: float):
    return render_markdown(filename)


def cached_markdown(filename: str):
    filepath = os.path.join(CONTENT_DIR, f"{filename}.md")
    try:
        mtime = os.path.getmtime(filepath)
    except OSError:
        return None, None
    return _cached_render(filename, mtime)

# ---------------------------------------------------------------------------
# Search index
# ---------------------------------------------------------------------------
_SEARCH_INDEX = {}


def _build_search_index():
    global _SEARCH_INDEX
    for item in SIDEBAR:
        content_html, _ = cached_markdown(item["id"])
        if content_html is None:
            continue
        plain = _STRIP_HTML_RE.sub("", content_html)
        plain = html.unescape(plain)
        _SEARCH_INDEX[item["id"]] = {
            "title": item["title"].lower(),
            "text": plain.lower(),
        }

# ---------------------------------------------------------------------------
# Listeners
# ---------------------------------------------------------------------------
@app.listener("before_server_start")
async def on_startup(app_instance):
    logger.info("Starting Fenrir Docs server ...")
    _build_search_index()
    logger.info(f"Search index built: {len(_SEARCH_INDEX)} pages")


@app.listener("after_server_stop")
async def on_shutdown(app_instance):
    logger.info("Fenrir Docs server stopped.")

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
@app.middleware("response")
async def add_security_headers(req, resp):
    resp.headers["X-Powered-By"] = "Fenrir Framework"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/static/<path:path>")
async def serve_static(path: str):
    return send_from_directory(os.path.join(BASE_DIR, "static"), path)


@app.get("/")
async def index():
    return await doc("introduction")


@app.get("/docs/<doc_id>")
async def doc(doc_id: str):
    content_html, toc_html = cached_markdown(doc_id)
    if content_html is None:
        raise HTTPNotFound(detail="Document not found")

    idx = _SIDEBAR_INDEX.get(doc_id, -1)
    prev_page = SIDEBAR[idx - 1] if idx > 0 else None
    next_page = SIDEBAR[idx + 1] if idx < len(SIDEBAR) - 1 else None
    current_page = SIDEBAR[idx] if idx != -1 else None

    filepath = os.path.join(CONTENT_DIR, f"{doc_id}.md")
    mtime = os.path.getmtime(filepath)
    last_updated = datetime.datetime.fromtimestamp(mtime).strftime("%b %d, %Y")

    host = request.host or request.headers.get("host", "localhost")
    canonical_url = f"https://{host}{request.path}"
    base_url = f"https://{host}"

    return render_template(
        "index.html",
        content=content_html,
        toc=toc_html,
        sidebar=SIDEBAR,
        current_id=doc_id,
        current_page=current_page,
        prev_page=prev_page,
        next_page=next_page,
        last_updated=last_updated,
        canonical_url=canonical_url,
        base_url=base_url,
    )

# ---------------------------------------------------------------------------
# Search API
# ---------------------------------------------------------------------------
@app.get("/api/search")
async def search():
    if not _SEARCH_INDEX:
        _build_search_index()

    query = request.args.get("q", "").lower().strip()
    if not query or len(query) < 2:
        return JSONResponse([])

    results = []
    for item in SIDEBAR:
        idx_data = _SEARCH_INDEX.get(item["id"])
        if idx_data is None:
            continue

        if query in idx_data["title"] or query in idx_data["text"]:
            text = idx_data["text"]
            pos = text.find(query)
            snippet = ""
            if pos != -1:
                start = max(0, pos - 40)
                end = min(len(text), pos + 60)
                snippet = "..." + text[start:end].strip() + "..."

            results.append({"title": item["title"], "id": item["id"], "snippet": snippet})

    return JSONResponse(results)

# ---------------------------------------------------------------------------
# SEO
# ---------------------------------------------------------------------------
@app.get("/sitemap.xml")
async def sitemap():
    root_url = f"https://{request.headers.get('host', 'localhost')}/"
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    pages = [{"loc": root_url, "lastmod": today, "priority": "1.0"}]
    for item in SIDEBAR:
        pages.append({
            "loc": f"{root_url}docs/{item['id']}",
            "lastmod": today,
            "priority": "0.8",
        })

    sitemap_xml = render_template("sitemap.xml", pages=pages)
    return Response(body=sitemap_xml, content_type="application/xml")


@app.get("/llms.txt")
async def llms():
    content = render_template("llms.txt")
    return Response(body=content, content_type="text/markdown; charset=utf-8")


@app.get("/robots.txt")
async def robots():
    root_url = f"https://{request.headers.get('host', 'localhost')}/"
    body = f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {root_url}sitemap.xml"
    return TextResponse(body)

# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.exception(404)
async def page_not_found(req, exc):
    host = request.host or request.headers.get("host", "localhost")
    canonical_url = f"https://{host}{request.path}"
    base_url = f"https://{host}"
    body = render_template(
        "index.html",
        content="<h1>404 - Page Not Found</h1><p>The documentation you are looking for does not exist.</p>",
        sidebar=SIDEBAR,
        current_id=None,
        canonical_url=canonical_url,
        base_url=base_url,
    )
    return Response(body=body, status=404)

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, app_path="app:app")