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
    {"title": "Introduction to Fenrir Python Web Framework", "id": "introduction", "icon": "info", "description": "Fenrir is a high-performance hybrid Python web framework combining Flask, FastAPI, Falcon, and Sanic paradigms into one unified ASGI application environment."},
    {"title": "Installation Guide for Fenrir Framework", "id": "installation", "icon": "download", "description": "Install Fenrir framework step by step using pip install fenrir-framework with all required ASGI server dependencies and optional extras for Redis sessions."},
    {"title": "Project Structure for Fenrir Applications", "id": "project-structure", "icon": "folder", "description": "Recommended file and directory layout for organizing Fenrir Python web applications with proper folder structure, modules, and configuration files."},
    {"title": "Quick Start Guide to Fenrir Framework", "id": "quick-start", "icon": "play", "description": "Build your first Fenrir application from scratch with routing setup, middleware configuration, request handling, and response generation in minutes."},
    {"title": "Basic Concepts in Fenrir Framework", "id": "basic-concepts", "icon": "book-open", "description": "Core Fenrir concepts including app constructor parameters, middleware setup, session management, request processing pipeline, and configuration options."},
    {"title": "Routing System in Fenrir Framework", "id": "routing", "icon": "git-commit", "description": "Fenrir routing system with path parameters, type converters, regex patterns, route decorators, and trie-based matching for building API endpoints."},
    {"title": "Request and Response Handling in Fenrir", "id": "request-response", "icon": "arrow-left-right", "description": "Handle HTTP request and response objects: access headers, body data, sessions, cookies, query parameters, and build custom response types."},
    {"title": "Dependency Injection in Fenrir Framework", "id": "dependency-injection", "icon": "plug", "description": "FastAPI-style dependency injection system using Depends, yield dependencies, request-scoped overrides, circular detection, and auto-resolution."},
    {"title": "Data Validation with Pydantic in Fenrir", "id": "data-validation", "icon": "check-circle", "description": "Automatic request data validation using Pydantic model integration for building type-safe, reliable, and well-documented API endpoints."},
    {"title": "Context Locals and Variables in Fenrir", "id": "context-locals", "icon": "database", "description": "Thread-safe and async-safe context variables including request, session, g, and current_app for ASGI applications with contextvars support."},
    {"title": "Class-Based Resources in Fenrir Framework", "id": "class-based-resources", "icon": "layers", "description": "Falcon-style class-based resources with on_get, on_post, on_put, on_delete methods for building clean and organized REST API endpoints."},
    {"title": "File Upload Handling in Fenrir Framework", "id": "file-upload", "icon": "upload", "description": "Handle file uploads in Fenrir using send_file, send_from_directory helpers, process multipart form data, and validate uploaded files."},
    {"title": "WebSocket Support in Fenrir ASGI Server", "id": "websocket", "icon": "zap", "description": "Build real-time WebSocket endpoints with Fenrir ASGI server for bidirectional communication, live data streaming, and real-time updates."},
    {"title": "Server-Sent Events SSE in Fenrir Framework", "id": "server-sent-events", "icon": "radio", "description": "Stream real-time server-sent events to connected clients using Fenrir EventSourceResponse for live notifications and data feeds."},
    {"title": "Jinja2 Templating in Fenrir Applications", "id": "templating", "icon": "layout", "description": "Render HTML pages using built-in Jinja2 template engine integration with automatic template loading, context variables, and inheritance."},
    {"title": "Error Handling and Exceptions in Fenrir", "id": "error-handling", "icon": "alert-circle", "description": "Handle HTTP error status codes and custom exceptions using Fenrir middleware with proper error response formatting and logging support."},
    {"title": "Error Handling Compatibility Across Frameworks", "id": "error-handling-compatibility", "icon": "shuffle", "description": "Multi-style error handling compatibility layer supporting Flask, FastAPI, and Falcon error handling patterns in a single Fenrir application."},
    {"title": "Middleware System in Fenrir Framework", "id": "middleware", "icon": "cpu", "description": "Fenrir middleware system for request processing, response modification, application-level hooks, interceptors, and ASGI middleware chaining."},
    {"title": "Middleware Classes CORS GZip RateLimit CSRF", "id": "middleware-classes", "icon": "layers", "description": "Built-in ASGI middleware classes including CORS, GZip compression, RequestID tracking, RateLimit, BodyLimit, and CSRF protection."},
    {"title": "Sessions Management in Fenrir Framework", "id": "sessions", "icon": "database", "description": "Session management with secure cookie backend, in-memory session storage, Redis session backend, and server-side session support for scalability."},
    {"title": "Pagination for API Endpoints in Fenrir", "id": "pagination", "icon": "list", "description": "Paginated list responses using PaginationParams utility for building efficient API endpoints with metadata, sorting, and filtering support."},
    {"title": "Background Tasks in Fenrir ASGI Server", "id": "background-tasks", "icon": "clock", "description": "Run background tasks and scheduled jobs without blocking request handlers in Fenrir ASGI server applications using BackgroundTasks utility."},
    {"title": "Authentication and Security in Fenrir Framework", "id": "authentication-security", "icon": "shield", "description": "Authentication methods in Fenrir: API key validation, JWT token handling, Bearer token, OAuth2 flows, OpenID Connect, and WebSocket auth."},
    {"title": "Blueprints Organization in Fenrir Framework", "id": "blueprints", "icon": "map", "description": "Modularize and organize routes using Fenrir blueprints for building large-scale applications with clean architecture and separation of concerns."},
    {"title": "Application Configuration in Fenrir Framework", "id": "configuration", "icon": "settings", "description": "Configure Fenrir applications: settings management, environment variables, ASGI server options, and runtime configuration parameters."},
    {"title": "Testing Guide for Fenrir Applications", "id": "testing", "icon": "clipboard-list", "description": "Write comprehensive tests using pytest and Fenrir TestClient for validating API endpoints, middleware behavior, and application logic."},
    {"title": "CLI Tools Reference for Fenrir Framework", "id": "cli-tools", "icon": "terminal", "description": "CLI commands reference for Fenrir: fenrir run, routes, shell, bench, new, info, and monitoring dashboard management commands and options."},
    {"title": "Advanced Features in Fenrir Framework", "id": "advanced-features", "icon": "sliders", "description": "Advanced features in Fenrir: dev mode debug pages, WSGI mounting, connection pooling, multiple response models, and HTTP/2 push support."},
    {"title": "Monitoring Dashboard in Fenrir Framework", "id": "monitoring", "icon": "activity", "description": "Built-in monitoring dashboard for Fenrir: health checks, traffic analysis, alerts system, and REST API monitoring endpoints for observability."},
    {"title": "Signals System for Event-Driven Programming", "id": "signals", "icon": "radio", "description": "Event-driven programming with Fenrir signals system for creating decoupled, extensible, and maintainable application components and handlers."},
    {"title": "JSON Provider for Custom Serialization", "id": "json-provider", "icon": "braces", "description": "Custom JSON serialization provider with tagged types support for building flexible API response formats and handling complex data structures."},
    {"title": "OpenAPI Customization for API Documentation", "id": "openapi-customization", "icon": "file-text", "description": "Customize Swagger UI, ReDoc, and OpenAPI route metadata for generating comprehensive and interactive API documentation for your endpoints."},
    {"title": "Best Practices for Fenrir Applications", "id": "best-practices", "icon": "award", "description": "Production-ready patterns and best practices for Fenrir: performance optimization, security hardening, type hints, and code organization."},
    {"title": "Framework Comparison Fenrir vs FastAPI Flask", "id": "comparison", "icon": "bar-chart", "description": "Compare Fenrir framework vs Flask vs FastAPI vs Sanic vs Falcon vs Bottle features, performance benchmarks, ecosystem, and use cases."},
    {"title": "Conclusion and Fenrir v3.1.3 Changelog", "id": "conclusion", "icon": "flag", "description": "Fenrir v3.1.3 complete changelog: middleware updates, sessions improvements, request handling enhancements, and authentication security fixes."},
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