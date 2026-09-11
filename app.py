"""
Fenrir Documentation Application — Optimized for Performance.

This is the main application file for the Fenrir framework documentation site.
It serves 43 documentation pages with full-text search, SEO endpoints,
and error monitoring via Sentry.

Architecture:
    - Fenrir (ASGI) as the web framework
    - Jinja2 templates for HTML rendering
    - Markdown for content files (content/*.md)
    - orjson for fast JSON serialization (optional, falls back to stdlib)
    - Sentry for error monitoring (optional)

Best practices applied:
    - Lazy imports for heavy modules (orjson, sentry_sdk)
    - LRU cached markdown rendering (invalidated by file mtime)
    - Pre-built search index (built once at startup, O(1) lookups)
    - Static asset caching headers (1 day TTL)
    - Minimal request-path work (no I/O in hot paths)
"""
from __future__ import annotations

import datetime
import html
import logging
import os
import re
from functools import lru_cache
from typing import Any

# Load .env file before reading any environment variables
from dotenv import load_dotenv

load_dotenv()

# Fenrir framework imports
from fenrir import (
    BodyLimitMiddleware,  # Request body size limit
    CORSMiddleware,  # Cross-Origin Resource Sharing
    Fenrir,
    GZipMiddleware,  # GZip compression
    HTTPNotFound,  # 404 exception
    JSONResponse,  # Standard JSON response
    RateLimitMiddleware,  # Rate limiting
    RequestIDMiddleware,  # Unique request ID header
    Response,  # Raw response (used with orjson)
    SecurityHeadersMiddleware,  # Security headers (HSTS, CSP, etc.)
    StaticFiles,  # Static file serving
    TextResponse,  # Plain text response
    render_template,  # Jinja2 template rendering
    request,  # Thread-local request context
)
from fenrir.performance import optimize_app  # Performance optimizations

# ---------------------------------------------------------------------------
# Optional dependencies (loaded lazily, gracefully degraded if missing)
# ---------------------------------------------------------------------------

def _import_orjson():
    """Try to import orjson (7x faster JSON than stdlib).
    Returns the module if available, None otherwise.
    Falls back to stdlib json via JSONResponse if not installed.
    """
    try:
        import orjson
        return orjson
    except ImportError:
        return None


orjson = _import_orjson()

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("docs-fenrir")


# ---------------------------------------------------------------------------
# Sentry error monitoring (optional, enabled via SENTRY_DSN env var)
# ---------------------------------------------------------------------------
def _init_sentry():
    """Initialize Sentry SDK for error monitoring.
    
    Returns:
        tuple: (enabled: bool, middleware_class: type or None)
    
    Configured via environment variables:
        - SENTRY_DSN: Sentry project DSN (required to enable)
        - ENVIRONMENT: Environment name (default: "production")
    
    Traces 10% of requests for performance monitoring.
    """
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return False, None
    try:
        import sentry_sdk
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.1,      # Sample 10% of requests
            profiles_sample_rate=0.1,     # Sample 10% for profiling
            environment=os.environ.get("ENVIRONMENT", "production"),
            release="docs-fenrir@4.4.0",
        )
        logger.info("Sentry error monitoring initialized")
        return True, SentryAsgiMiddleware
    except ImportError:
        logger.warning("sentry-sdk not installed, error monitoring disabled")
        return False, None
    except (ValueError, OSError) as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False, None


_sentry_enabled, _SentryAsgiMiddleware = _init_sentry()

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------
app = Fenrir(
    title="Fenrir Docs",
    version="4.4.0",
    dev_mode=os.environ.get("FENRIR_DEV", "0") == "1",
    # Built-in OpenAPI/Swagger/ReDoc endpoints
    docs_url="/docs/swagger",      # Swagger UI
    redoc_url="/docs/redoc",       # ReDoc
    openapi_url="/api/openapi.json", # OpenAPI schema
    docs_enabled=True,             # Enable even in production
)

# --- ASGI Middleware Stack ---
# Middleware is applied in reverse order (last added = outermost = first to execute)
# Sentry must be first to capture errors from all other middleware

if _sentry_enabled and _SentryAsgiMiddleware is not None:
    app.add_middleware(_SentryAsgiMiddleware)   # 1. Error monitoring (outermost)

# Security & performance middleware (executed in this order for each request):
app.add_middleware(CORSMiddleware, allow_origins=["*"])            # 2. CORS headers
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)  # 3. GZip compression
app.add_middleware(BodyLimitMiddleware, max_content_length=1_048_576)  # 4. 1MB body limit
app.add_middleware(RequestIDMiddleware)                            # 5. Unique request ID
app.add_middleware(RateLimitMiddleware, max_requests=1000, window_seconds=60)  # 6. 1000 req/min
app.add_middleware(                                               # 7. Security headers
    SecurityHeadersMiddleware,
    hsts_max_age=31536000,           # 1 year HSTS
    hsts_include_subdomains=True,
    frame_options="DENY",            # Prevent clickjacking
    content_type_options="nosniff",  # Prevent MIME sniffing
    referrer_policy="strict-origin-when-cross-origin",
    permissions_policy="geolocation=(), microphone=(), camera=()",
    cross_origin_opener_policy="same-origin",
    xss_protection="1; mode=block",
)


def _init_fenrir_monitoring():
    """Initialize Fenrir's built-in monitoring dashboard (optional).
    Silently ignored if fenrir.features is not available.
    """
    try:
        from fenrir.features import init_fenrir_monitoring
        init_fenrir_monitoring(app)
    except (ImportError, AttributeError):
        pass  # pragma: no cover


_init_fenrir_monitoring()

# Apply performance optimizations (OpenAPI caching, handler pre-resolution, etc.)
optimize_app(app)

# ---------------------------------------------------------------------------
# Constants (computed once at import time)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ---------------------------------------------------------------------------
# Sidebar configuration (43 documentation pages)
# Each entry defines:
#   - title: Full page title (used in SEO and page header)
#   - id: URL slug and filename (content/{id}.md)
#   - icon: Lucide icon name (displayed in sidebar)
#   - description: Meta description for SEO (120-150 chars)
# ---------------------------------------------------------------------------
SIDEBAR: list[dict[str, Any]] = [
    {"title": "Introduction to Fenrir Python Web Framework", "id": "introduction", "icon": "info", "description": "Introduction to Fenrir, a hybrid Python web framework combining Flask, FastAPI, Falcon, and Sanic paradigms into one unified ASGI application."},
    {"title": "Installation Guide for Fenrir Framework", "id": "installation", "icon": "download", "description": "Step-by-step installation guide for Fenrir using pip install fenrir-framework with all required dependencies and optional extras for Redis."},
    {"title": "Project Structure for Fenrir Applications", "id": "project-structure", "icon": "folder", "description": "Recommended file and directory layout for organizing Fenrir Python web applications with proper folder structure, modules, and configuration files."},
    {"title": "Quick Start Guide for Fenrir Framework", "id": "quick-start", "icon": "play", "description": "Build your first Fenrir application from scratch with routing setup, middleware configuration, request handling, and response generation."},
    {"title": "Basic Concepts in Fenrir Web Framework", "id": "basic-concepts", "icon": "book-open", "description": "Core Fenrir concepts including app constructor parameters, middleware setup, session management, request processing, and configuration options."},
    {"title": "Routing System in Fenrir Web Framework", "id": "routing", "icon": "git-commit", "description": "Fenrir routing system with path parameters, type converters, regex patterns, route decorators, and trie-based matching for efficient API endpoints."},
    {"title": "Request and Response Handling in Fenrir", "id": "request-response", "icon": "arrow-left-right", "description": "Handle HTTP request and response objects in Fenrir: access headers, body data, sessions, cookies, query parameters, and build custom response types."},
    {"title": "Dependency Injection System in Fenrir", "id": "dependency-injection", "icon": "plug", "description": "FastAPI-style dependency injection using Depends, yield dependencies, request-scoped overrides, circular detection, and automatic resolution."},
    {"title": "Data Validation with Pydantic in Fenrir", "id": "data-validation", "icon": "check-circle", "description": "Automatic request data validation using Pydantic model integration for building type-safe, reliable, and well-documented API endpoints."},
    {"title": "Context Locals and Variables in Fenrir", "id": "context-locals", "icon": "database", "description": "Thread-safe and async-safe context variables including request, session, g, and current_app for ASGI applications with proper contextvars isolation."},
    {"title": "Class-Based Resources Pattern in Fenrir", "id": "class-based-resources", "icon": "layers", "description": "Falcon-style class-based resources with on_get, on_post, on_put, on_delete methods for building clean, organized, and maintainable REST API endpoints."},
    {"title": "File Upload Handling Guide for Fenrir", "id": "file-upload", "icon": "upload", "description": "Handle file uploads using send_file, send_from_directory helpers, process multipart form data, and validate uploaded files with proper error handling."},
    {"title": "WebSocket Support in Fenrir Framework", "id": "websocket", "icon": "zap", "description": "Build real-time WebSocket endpoints with Fenrir ASGI server for bidirectional communication, live data streaming, and real-time updates."},
    {"title": "Server-Sent Events SSE Guide for Fenrir", "id": "server-sent-events", "icon": "radio", "description": "Stream real-time server-sent events to connected clients using Fenrir EventSourceResponse for live notifications, data feeds, and real-time updates."},
    {"title": "Jinja2 Templating Engine Guide for Fenrir", "id": "templating", "icon": "layout", "description": "Render HTML pages using built-in Jinja2 template engine with automatic template loading, context variables, inheritance, and custom filters."},
    {"title": "Error Handling and Exceptions in Fenrir", "id": "error-handling", "icon": "alert-circle", "description": "Handle HTTP error status codes and custom exceptions with proper error response formatting, logging support, and developer-friendly debug pages."},
    {"title": "Error Handling Compatibility Layer Guide", "id": "error-handling-compatibility", "icon": "shuffle", "description": "Multi-style error handling compatibility layer supporting Flask, FastAPI, and Falcon error handling patterns in a single application."},
    {"title": "Middleware System in Fenrir Framework", "id": "middleware", "icon": "cpu", "description": "Fenrir middleware system for request processing, response modification, application-level hooks, interceptors, and ASGI middleware chaining."},
    {"title": "Middleware Classes Reference Guide Fenrir", "id": "middleware-classes", "icon": "layers", "description": "Built-in ASGI middleware classes including CORS, GZip compression, RequestID, RateLimit, BodyLimit, CSRF, and SecurityHeaders protection."},
    {"title": "Sessions Management in Fenrir Framework", "id": "sessions", "icon": "database", "description": "Session management with secure cookie backend, in-memory session storage, Redis session backend, and server-side session support for scalable apps."},
    {"title": "Pagination for API Endpoints Guide Fenrir", "id": "pagination", "icon": "list", "description": "Paginated list responses using PaginationParams for building efficient API endpoints with metadata, sorting, filtering, and pagination support."},
    {"title": "Background Tasks and Workers Guide Fenrir", "id": "background-tasks", "icon": "clock", "description": "Run background tasks and scheduled jobs without blocking request handlers using BackgroundTasks utility for efficient async processing."},
    {"title": "Authentication and Security Guide Fenrir", "id": "authentication-security", "icon": "shield", "description": "Authentication methods including API key validation, JWT tokens, Bearer token, OAuth2 flows, OpenID Connect, and WebSocket authentication."},
    {"title": "Blueprints for Modular Applications Fenrir", "id": "blueprints", "icon": "map", "description": "Modularize and organize routes using blueprints for building large-scale applications with clean architecture, separation of concerns, and reuse."},
    {"title": "Application Configuration Guide for Fenrir", "id": "configuration", "icon": "settings", "description": "Configure Fenrir applications with settings management, environment variables, ASGI server options, and runtime configuration parameters."},
    {"title": "Testing Guide for Fenrir Applications", "id": "testing", "icon": "clipboard-list", "description": "Write comprehensive tests using pytest and Fenrir TestClient for validating API endpoints, middleware behavior, and application logic."},
    {"title": "CLI Tools Reference for Fenrir Framework", "id": "cli-tools", "icon": "terminal", "description": "Complete CLI commands reference for Fenrir: run, routes, shell, bench, new, info, and monitoring dashboard management commands."},
    {"title": "Advanced Features in Fenrir Framework", "id": "advanced-features", "icon": "sliders", "description": "Advanced features including dev mode debug pages, WSGI mounting, connection pooling, multiple response models, and HTTP/2 push support."},
    {"title": "Monitoring Dashboard in Fenrir Framework", "id": "monitoring", "icon": "activity", "description": "Built-in monitoring dashboard with health checks, traffic analysis, alerts system, uptime statistics, and REST API monitoring endpoints."},
    {"title": "Signals System for Event-Driven Apps Fenrir", "id": "signals", "icon": "radio", "description": "Event-driven programming with signals system for creating decoupled, extensible, and maintainable application components and handlers."},
    {"title": "Custom JSON Provider for Fenrir Framework", "id": "json-provider", "icon": "braces", "description": "Custom JSON serialization provider with tagged types support, orjson integration, and flexible API response formats for complex data."},
    {"title": "OpenAPI Customization for Fenrir Framework", "id": "openapi-customization", "icon": "file-text", "description": "Customize Swagger UI, ReDoc, and OpenAPI route metadata for generating comprehensive and interactive API documentation endpoints."},
    {"title": "Plugin System for Fenrir Web Framework", "id": "plugin-system", "icon": "puzzle", "description": "Plugin system with version compatibility, dependency resolution, config validation, hot-reload, auto-discovery, and health monitoring."},
    {"title": "Hook System for Fenrir Web Framework", "id": "hook-system", "icon": "anchor", "description": "Hook and extension point system with priority ordering, one-time hooks, wildcard hooks, async/sync support, and middleware integration."},
    {"title": "Lightweight ORM for Fenrir Applications", "id": "orm", "icon": "database", "description": "Lightweight async ORM with SQLite and PostgreSQL support, Model metaclass, QuerySet with filters and ordering, and SQL injection prevention."},
    {"title": "Caching System for Fenrir Applications", "id": "caching", "icon": "hard-drive", "description": "Caching system with MemoryCache LRU and TTL, RedisCache with SCAN, FileCache with atomic writes, and prefix invalidation support."},
    {"title": "Queue and Job System for Fenrir Framework", "id": "queue-system", "icon": "list", "description": "Queue and job system with retry and backoff, job priorities, timeouts, worker pools with concurrency, and MemoryQueue or RedisQueue backends."},
    {"title": "GraphQL Support for Fenrir Applications", "id": "graphql-support", "icon": "share-2", "description": "GraphQL support via strawberry-graphql with GraphiQL playground, type-safe resolvers, mutations, subscriptions, and seamless integration."},
    {"title": "gRPC Support for Fenrir Applications", "id": "grpc-support", "icon": "server", "description": "gRPC support with GRPCServer, GRPCService, GRPCClient, request interceptors, health checking, and Fenrir ASGI integration."},
    {"title": "Performance and orjson in Fenrir Framework", "id": "performance", "icon": "zap", "description": "Performance optimization with orjson for 7x faster JSON, ObjectPool, ResponseCache, PerformanceMonitor, and optimize_app() utility."},
    {"title": "Best Practices for Fenrir Applications", "id": "best-practices", "icon": "award", "description": "Production-ready patterns and best practices: performance optimization, security hardening, type hints, code organization, and deployment."},
    {"title": "Framework Comparison Fenrir vs Others Guide", "id": "comparison", "icon": "bar-chart", "description": "Compare Fenrir vs Flask vs FastAPI vs Sanic vs Falcon vs Bottle features, performance benchmarks, ecosystem, and migration guides."},
    {"title": "Conclusion and Release Changelog Fenrir", "id": "conclusion", "icon": "flag", "description": "Fenrir v4.4.0 complete changelog with security hardening, CSRF graceful fallback, bug fixes, performance optimizations, and test coverage."},
]

# Pre-compute sidebar index for O(1) lookup (instead of O(n) list scan)
_SIDEBAR_INDEX: dict[str, int] = {item["id"]: i for i, item in enumerate(SIDEBAR)}

# ---------------------------------------------------------------------------
# Markdown rendering (cached at module level for performance)
# ---------------------------------------------------------------------------

# Markdown extensions for content rendering
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension  # Syntax highlighting
from markdown.extensions.fenced_code import FencedCodeExtension  # Fenced code blocks
from markdown.extensions.tables import TableExtension  # Table support
from markdown.extensions.toc import TocExtension  # Table of contents

_MD_EXTENSIONS: list[str | markdown.extensions.Extension] = [
    "extra",                                    # Standard extras (bold, italic, links, etc.)
    FencedCodeExtension(),                      # ``` code blocks
    CodeHiliteExtension(css_class="highlight", linenums=True),  # Syntax highlighting
    TableExtension(),                           # | tables |
    TocExtension(baselevel=1, marker=None),     # Auto-generated TOC
]

# Pre-compiled regex patterns (compiled once, reused on every request)
_EXTERNAL_LINK_RE = re.compile(
    r'<a\s+(?![^>]*rel=)([^>]*href="https?://[^"]+"[^>]*)>'
)
_TABLE_RE = re.compile(r'(<table\b.*?</table>)', re.DOTALL)
_STRIP_HTML_RE = re.compile(r'<[^>]+>')


def _render_markdown_raw(filename: str) -> tuple[str | None, str | None]:
    """Render a markdown file to HTML + TOC (uncached).
    
    Args:
        filename: Document ID (without .md extension)
    
    Returns:
        Tuple of (html_content, toc_html) or (None, None) if file not found
    
    Processing:
        1. Read markdown file from content/ directory
        2. Convert to HTML with extensions (code highlighting, tables, TOC)
        3. Add rel="noopener noreferrer" to external links (security)
        4. Wrap tables in responsive div containers
    """
    filepath = os.path.join(CONTENT_DIR, f"{filename}.md")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None, None

    md = markdown.Markdown(extensions=_MD_EXTENSIONS)
    html_content = md.convert(content)

    # Security: Add rel="noopener noreferrer" to external links
    html_content = _EXTERNAL_LINK_RE.sub(
        r'<a \1 rel="noopener noreferrer" target="_blank">', html_content
    )
    # Responsive: Wrap tables in scrollable containers
    html_content = _TABLE_RE.sub(
        r'<div class="table-wrapper">\1</div>', html_content
    )

    return html_content, getattr(md, "toc", "")


@lru_cache(maxsize=128)
def _cached_render(filename: str, _mtime: float) -> tuple[str | None, str | None]:
    """LRU-cached markdown render (invalidated by file modification time).
    
    Cache key = (filename, mtime), so cache auto-invalidates when file changes.
    Max 128 entries cached (more than enough for 43 pages).
    """
    return _render_markdown_raw(filename)


def cached_markdown(filename: str) -> tuple[str | None, str | None]:
    """Get cached markdown HTML + TOC for a page.
    
    This is the main entry point for markdown rendering.
    Uses mtime-based cache invalidation: if file hasn't changed, returns cached.
    """
    filepath = os.path.join(CONTENT_DIR, f"{filename}.md")
    try:
        mtime = os.path.getmtime(filepath)
    except OSError:
        return None, None
    return _cached_render(filename, mtime)


# ---------------------------------------------------------------------------
# Search index (built once at startup, used on every search request)
# ---------------------------------------------------------------------------

_SEARCH_INDEX: dict[str, dict[str, str]] = {}


def _build_search_index() -> None:
    """Build full-text search index from all documentation pages.
    
    Creates an inverted index with:
        - page_id -> {"title": lowercase_title, "text": lowercase_plain_text}
    
    Search is case-insensitive and matches against both title and content.
    Built once at startup to avoid per-request I/O.
    """
    global _SEARCH_INDEX  # noqa: PLW0602
    _SEARCH_INDEX.clear()
    for item in SIDEBAR:
        content_html, _ = cached_markdown(item["id"])
        if content_html is None:
            continue
        # Strip HTML tags and decode entities for plain text search
        plain = html.unescape(_STRIP_HTML_RE.sub("", content_html))
        _SEARCH_INDEX[item["id"]] = {
            "title": item["title"].lower(),
            "text": plain.lower(),
        }


# ---------------------------------------------------------------------------
# Helper functions (inlined for hot paths)
# ---------------------------------------------------------------------------
def _get_host() -> str:
    """Extract host from current request (fast path).
    Falls back to 'localhost' if no host header present.
    """
    return request.host or request.headers.get("host", "localhost")


def _make_url(host: str, path: str) -> str:
    """Build canonical URL from host and path."""
    scheme = "http" if host.startswith("localhost") else "https"
    return f"{scheme}://{host}{path}"


# ---------------------------------------------------------------------------
# Startup: Build search index and register lifecycle listeners
# ---------------------------------------------------------------------------
_build_search_index()
logger.info("Search index built: %d pages", len(_SEARCH_INDEX))


@app.listener("before_server_start")
async def on_startup(app_instance: Any) -> None:
    """Called before the ASGI server starts accepting connections."""
    logger.info("Starting Fenrir Docs server ...")


@app.listener("after_server_stop")
async def on_shutdown(app_instance: Any) -> None:
    """Called after the ASGI server stops accepting connections."""
    logger.info("Fenrir Docs server stopped.")


# ---------------------------------------------------------------------------
# Static files (served with 1-day cache header)
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR, cache_control="public, max-age=86400"))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
async def index() -> Any:
    """Homepage: redirect to Introduction page."""
    return await doc("introduction")


@app.get("/playground")
async def playground() -> Any:
    """Interactive code playground (Pyodide-based).
    
    Allows users to try Fenrir code directly in the browser.
    Python runs via WebAssembly (Pyodide), no server needed.
    """
    host = _get_host()
    return render_template(
        "playground.html",
        sidebar=SIDEBAR,
        current_id=None,
        current_page={"title": "Interactive Python Playground - Run Fenrir Code Online", "id": "playground", "icon": "play-circle", "description": "Try Fenrir framework code directly in your browser with our interactive Python playground. Write, run, and test Fenrir code online instantly."},
        canonical_url=_make_url(host, "/playground"),
        base_url=_make_url(host, "/"),
    )


@app.get("/docs/<doc_id>")
async def doc(doc_id: str) -> Any:
    """Render a documentation page by ID.
    
    URL pattern: /docs/{doc_id}
    Example: /docs/introduction
    
    Returns rendered HTML with sidebar navigation, table of contents,
    and prev/next page links.
    
    Raises:
        HTTPNotFound: If doc_id doesn't match any content file
    """
    content_html, toc_html = cached_markdown(doc_id)
    if content_html is None:
        raise HTTPNotFound(detail="Document not found")

    # Calculate prev/next navigation
    idx = _SIDEBAR_INDEX.get(doc_id, -1)
    prev_page = SIDEBAR[idx - 1] if idx > 0 else None
    next_page = SIDEBAR[idx + 1] if idx < len(SIDEBAR) - 1 else None
    current_page = SIDEBAR[idx] if idx != -1 else None

    # Get file modification time (for "Last Updated" display)
    filepath = os.path.join(CONTENT_DIR, f"{doc_id}.md")
    try:
        mtime = os.path.getmtime(filepath)
        last_updated = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).strftime("%b %d, %Y")
        last_updated_iso = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
    except OSError:  # pragma: no cover
        last_updated = ""
        last_updated_iso = ""

    host = _get_host()

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
        last_updated_iso=last_updated_iso,
        canonical_url=_make_url(host, request.path),
        base_url=_make_url(host, "/"),
    )


# ---------------------------------------------------------------------------
# Search API (full-text search across all documentation)
# ---------------------------------------------------------------------------
@app.get("/api/search")
async def search() -> Any:
    """
    Search documentation pages.
    
    Full-text search across all documentation pages matching the query
    in titles and content text. Returns matching results with snippets.
    
    Query Parameters:
        q (str): Search query (minimum 2 characters)
    
    Returns:
        list: Array of search results with title, id, and snippet
    
    Example:
        GET /api/search?q=middleware
        
        Response:
        [
            {
                "title": "Middleware System in Fenrir Framework",
                "id": "middleware",
                "snippet": "...middleware system for request processing..."
            }
        ]
    """
    query = request.args.get("q", "").lower().strip()
    if not query or len(query) < 2:
        return JSONResponse([])

    results = []

    # Search through sidebar items (preserves page order)
    for item in SIDEBAR:
        idx_data = _SEARCH_INDEX.get(item["id"])
        if idx_data is None:
            continue

        # Match against title and content (case-insensitive)
        if query in idx_data["title"] or query in idx_data["text"]:
            text = idx_data["text"]
            pos = text.find(query)
            # Extract snippet: 40 chars before + 60 chars after match
            snippet = ""
            if pos != -1:
                start = max(0, pos - 40)
                end = min(len(text), pos + 60)
                snippet = "..." + text[start:end].strip() + "..."

            results.append({
                "title": item["title"],
                "id": item["id"],
                "snippet": snippet,
            })

    # Use orjson for 7x faster JSON serialization if available
    if orjson is not None:
        body = orjson.dumps(results)
        return Response(body=body, content_type="application/json")
    else:
        return JSONResponse(results)  # pragma: no cover


# ---------------------------------------------------------------------------
# SEO endpoints (sitemap, robots.txt, llms.txt)
# ---------------------------------------------------------------------------
@app.get("/sitemap.xml")
async def sitemap() -> Any:
    """Generate XML sitemap for search engines.
    Lists all documentation pages with last-modified dates.
    """
    host = _get_host()
    scheme = "http" if host.startswith("localhost") else "https"
    root_url = f"{scheme}://{host}/"
    today = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d")

    pages = [{"loc": root_url, "lastmod": today, "priority": "1.0"}]
    pages.append({"loc": f"{root_url}playground", "lastmod": today, "priority": "0.7"})
    for item in SIDEBAR:
        pages.append({
            "loc": f"{root_url}docs/{item['id']}",
            "lastmod": today,
            "priority": "0.8",
        })

    sitemap_xml = render_template("sitemap.xml", pages=pages)
    return Response(body=sitemap_xml, content_type="application/xml")


@app.get("/llms.txt")
async def llms() -> Any:
    """LLM-friendly documentation index (for AI crawlers).
    Lists all pages with titles and descriptions in plain text.
    """
    content = render_template("llms.txt")
    return Response(body=content, content_type="text/markdown; charset=utf-8")


@app.get("/robots.txt")
async def robots() -> Any:
    """Robots exclusion protocol.
    Allows all crawlers but blocks /api/ endpoints.
    """
    host = _get_host()
    scheme = "http" if host.startswith("localhost") else "https"
    root_url = f"{scheme}://{host}/"
    body = f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {root_url}sitemap.xml"
    return TextResponse(body)


@app.get("/health")
async def health_check() -> Any:
    """Health check endpoint for monitoring.
    Returns application status and basic metrics.
    """
    import time
    return JSONResponse({
        "status": "healthy",
        "version": "4.4.0",
        "pages": len(SIDEBAR),
        "search_index": len(_SEARCH_INDEX),
        "uptime": time.time(),
    })


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.exception(404)
async def page_not_found(req: Any, exc: Any) -> Any:
    """Custom 404 error page with sidebar navigation."""
    host = _get_host()
    body = render_template(
        "index.html",
        content="<h1>404 - Page Not Found</h1><p>The documentation you are looking for does not exist.</p>",
        sidebar=SIDEBAR,
        current_id=None,
        canonical_url=_make_url(host, request.path),
        base_url=_make_url(host, "/"),
    )
    return Response(body=body, status=404)


# ---------------------------------------------------------------------------
# Entrypoint (for running directly: python app.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, app_path="app:app")
