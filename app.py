"""
Fenrir Documentation Application — Optimized for Performance.

Best practices applied:
- Lazy imports for heavy modules
- Centralized orjson JSON serialization
- LRU cached markdown rendering
- Pre-built search index
- Static asset caching headers
- Minimal request-path work
"""
from __future__ import annotations

import os
import re
import html
import datetime
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

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
from fenrir.json import json_dumps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("docs-fenrir")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = Fenrir(
    title="Fenrir Docs",
    version="4.1.0",
    dev_mode=os.environ.get("FENRIR_DEV", "0") == "1",
)

# --- Middleware (outermost first) ---
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)
app.add_middleware(BodyLimitMiddleware, max_content_length=1_048_576)
app.add_middleware(RequestIDMiddleware)

try:
    from fenrir.features import init_fenrir_monitoring
    init_fenrir_monitoring(app)
except Exception:
    pass

# ---------------------------------------------------------------------------
# Constants (computed once at import time)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content")
STATIC_DIR = os.path.join(BASE_DIR, "static")

SIDEBAR: List[Dict[str, Any]] = [
    {"title": "Introduction to Fenrir Python Web Framework for ASGI Applications", "id": "introduction", "icon": "info", "description": "Comprehensive introduction to Fenrir, a high-performance hybrid Python web framework combining Flask, FastAPI, Falcon, and Sanic paradigms into one unified ASGI application environment for modern web development."},
    {"title": "Installation Guide for Fenrir Python Web Framework", "id": "installation", "icon": "download", "description": "Step-by-step installation guide for Fenrir framework using pip install fenrir-framework with all required ASGI server dependencies and optional extras for Redis sessions and database support."},
    {"title": "Project Structure for Fenrir Python Web Applications", "id": "project-structure", "icon": "folder", "description": "Recommended file and directory layout for organizing Fenrir Python web applications with proper folder structure, modules, templates, and configuration files following best practices."},
    {"title": "Complete Quick Start Guide to Fenrir Python Web Framework", "id": "quick-start", "icon": "play", "description": "Build your first Fenrir application from scratch with routing setup, middleware configuration, request handling, and response generation in just a few minutes with this complete walkthrough."},
    {"title": "Essential Basic Concepts in Fenrir Python Web Framework", "id": "basic-concepts", "icon": "book-open", "description": "Core Fenrir concepts including app constructor parameters, middleware setup, session management, request processing pipeline, and configuration options for building modern web applications."},
    {"title": "Advanced Routing System in Fenrir Python Web Framework", "id": "routing", "icon": "git-commit", "description": "Fenrir routing system with path parameters, type converters, regex patterns, route decorators, and trie-based matching for building efficient and scalable API endpoints."},
    {"title": "Complete Request and Response Handling in Fenrir Framework", "id": "request-response", "icon": "arrow-left-right", "description": "Handle HTTP request and response objects in Fenrir: access headers, body data, sessions, cookies, query parameters, and build custom response types for your API endpoints."},
    {"title": "Dependency Injection in Fenrir Python Web Framework", "id": "dependency-injection", "icon": "plug", "description": "FastAPI-style dependency injection system in Fenrir using Depends, yield dependencies, request-scoped overrides, circular detection, and automatic parameter resolution."},
    {"title": "Automatic Data Validation with Pydantic in Fenrir Framework", "id": "data-validation", "icon": "check-circle", "description": "Automatic request data validation in Fenrir using Pydantic model integration for building type-safe, reliable, and well-documented API endpoints with minimal boilerplate code."},
    {"title": "Thread-Safe Context Locals and Variables in Fenrir Framework", "id": "context-locals", "icon": "database", "description": "Thread-safe and async-safe context variables in Fenrir including request, session, g, and current_app for ASGI applications with contextvars support for proper isolation."},
    {"title": "Class-Based Resources in Fenrir Python Web Framework", "id": "class-based-resources", "icon": "layers", "description": "Falcon-style class-based resources in Fenrir with on_get, on_post, on_put, on_delete methods for building clean, organized, and maintainable REST API endpoints."},
    {"title": "File Upload Handling in Fenrir Python Web Framework", "id": "file-upload", "icon": "upload", "description": "Handle file uploads in Fenrir using send_file, send_from_directory helpers, process multipart form data, and validate uploaded files with proper error handling and security."},
    {"title": "Real-Time WebSocket Support in Fenrir ASGI Python Server", "id": "websocket", "icon": "zap", "description": "Build real-time WebSocket endpoints with Fenrir ASGI server for bidirectional communication, live data streaming, authentication, and real-time updates in your applications."},
    {"title": "Real-Time Server-Sent Events SSE in Fenrir Python Framework", "id": "server-sent-events", "icon": "radio", "description": "Stream real-time server-sent events to connected clients using Fenrir EventSourceResponse for live notifications, data feeds, and real-time updates in your web applications."},
    {"title": "Jinja2 Templating Engine Integration in Fenrir Applications", "id": "templating", "icon": "layout", "description": "Render HTML pages in Fenrir using built-in Jinja2 template engine integration with automatic template loading, context variables, inheritance, and custom filters."},
    {"title": "Comprehensive Error Handling and Exceptions in Fenrir Framework", "id": "error-handling", "icon": "alert-circle", "description": "Handle HTTP error status codes and custom exceptions in Fenrir using middleware with proper error response formatting, logging support, and developer-friendly debug pages."},
    {"title": "Error Handling Compatibility in Fenrir Across Python Frameworks", "id": "error-handling-compatibility", "icon": "shuffle", "description": "Multi-style error handling compatibility layer in Fenrir supporting Flask, FastAPI, and Falcon error handling patterns in a single application for easy migration and integration."},
    {"title": "Powerful Middleware System in Fenrir Python Web Framework", "id": "middleware", "icon": "cpu", "description": "Fenrir middleware system for request processing, response modification, application-level hooks, interceptors, and ASGI middleware chaining for building robust web applications."},
    {"title": "Middleware Classes CORS GZip RateLimit CSRF in Fenrir", "id": "middleware-classes", "icon": "layers", "description": "Built-in ASGI middleware classes in Fenrir including CORS, GZip compression, RequestID tracking, RateLimit, BodyLimit, and CSRF protection for production-ready applications."},
    {"title": "Sessions Management in Fenrir Python Web Framework", "id": "sessions", "icon": "database", "description": "Session management in Fenrir with secure cookie backend, in-memory session storage, Redis session backend, and server-side session support for scalable web applications."},
    {"title": "Efficient Pagination for API Endpoints in Fenrir Framework", "id": "pagination", "icon": "list", "description": "Paginated list responses in Fenrir using PaginationParams utility for building efficient API endpoints with metadata, sorting, filtering, and cursor-based pagination support."},
    {"title": "Background Tasks and Job Queue in Fenrir ASGI Python Server", "id": "background-tasks", "icon": "clock", "description": "Run background tasks and scheduled jobs without blocking request handlers in Fenrir ASGI server applications using BackgroundTasks utility for efficient async processing."},
    {"title": "Authentication and Security in Fenrir Python Framework", "id": "authentication-security", "icon": "shield", "description": "Authentication methods in Fenrir including API key validation, JWT token handling, Bearer token, OAuth2 flows, OpenID Connect, and WebSocket authentication for secure applications."},
    {"title": "Blueprints Organization in Fenrir Python Web Framework", "id": "blueprints", "icon": "map", "description": "Modularize and organize routes in Fenrir using blueprints for building large-scale applications with clean architecture, separation of concerns, and reusable components."},
    {"title": "Application Configuration in Fenrir Python Framework", "id": "configuration", "icon": "settings", "description": "Configure Fenrir applications with settings management, environment variables, ASGI server options, and runtime configuration parameters for flexible and maintainable apps."},
    {"title": "Comprehensive Testing Guide for Fenrir Python Applications", "id": "testing", "icon": "clipboard-list", "description": "Write comprehensive tests for Fenrir applications using pytest and Fenrir TestClient for validating API endpoints, middleware behavior, and application logic with best practices."},
    {"title": "Complete CLI Tools Reference for Fenrir Python Framework", "id": "cli-tools", "icon": "terminal", "description": "Complete CLI commands reference for Fenrir: fenrir run, routes, shell, bench, new, info, and monitoring dashboard management commands with detailed options and examples."},
    {"title": "Powerful Advanced Features in Fenrir Python Web Framework", "id": "advanced-features", "icon": "sliders", "description": "Advanced features in Fenrir including dev mode debug pages, WSGI mounting, connection pooling, multiple response models, HTTP/2 push support, and performance optimizations."},
    {"title": "Built-in Monitoring Dashboard in Fenrir Python Framework", "id": "monitoring", "icon": "activity", "description": "Built-in monitoring dashboard for Fenrir with health checks, traffic analysis, alerts system, uptime statistics, and REST API monitoring endpoints for complete observability."},
    {"title": "Signals System for Event-Driven Programming in Fenrir", "id": "signals", "icon": "radio", "description": "Event-driven programming with Fenrir signals system for creating decoupled, extensible, and maintainable application components, handlers, and event-driven architectures."},
    {"title": "Custom JSON Provider for Serialization in Fenrir Framework", "id": "json-provider", "icon": "braces", "description": "Custom JSON serialization provider in Fenrir with tagged types support, orjson integration, and flexible API response formats for handling complex data structures efficiently."},
    {"title": "OpenAPI Customization for API Documentation in Fenrir", "id": "openapi-customization", "icon": "file-text", "description": "Customize Swagger UI, ReDoc, and OpenAPI route metadata in Fenrir for generating comprehensive and interactive API documentation for your REST API endpoints."},
    {"title": "Plugin System for Extending Fenrir Python Framework", "id": "plugin-system", "icon": "puzzle", "description": "Plugin system for Fenrir with version compatibility, dependency resolution, config validation, hot-reload, auto-discovery via entry points, health monitoring, and thread safety."},
    {"title": "Hook System for Extension Points in Fenrir Framework", "id": "hook-system", "icon": "anchor", "description": "Hook and extension point system in Fenrir with priority ordering, one-time hooks, wildcard hooks, async/sync support, middleware integration, and hook cancellation."},
    {"title": "Lightweight Async ORM for Database Access in Fenrir Framework", "id": "orm", "icon": "database", "description": "Lightweight async ORM in Fenrir with SQLite and PostgreSQL support, Model metaclass, QuerySet with filters and ordering, parameterized queries, and SQL injection prevention."},
    {"title": "High-Performance Caching System for Fenrir Python Framework", "id": "caching", "icon": "hard-drive", "description": "Caching system in Fenrir with MemoryCache using LRU and TTL, RedisCache with SCAN not KEYS, FileCache with atomic writes, and prefix invalidation for optimal performance."},
    {"title": "Production-Ready Queue and Job System for Fenrir Framework", "id": "queue-system", "icon": "list", "description": "Queue and job system in Fenrir with retry and backoff, job priorities, timeouts, worker pools with concurrency control, and MemoryQueue or RedisQueue backends for background processing."},
    {"title": "Full GraphQL Support in Fenrir Python Web Framework", "id": "graphql-support", "icon": "share-2", "description": "GraphQL support in Fenrir via strawberry-graphql with GraphiQL playground, type-safe resolvers, mutations, subscriptions, and seamless integration with Fenrir applications."},
    {"title": "Complete gRPC Support in Fenrir Python ASGI Framework", "id": "grpc-support", "icon": "server", "description": "gRPC support in Fenrir with GRPCServer, GRPCService, GRPCClient, request interceptors, health checking, and seamless integration with Fenrir ASGI applications."},
    {"title": "Performance and orjson Integration in Fenrir Framework", "id": "performance", "icon": "zap", "description": "Performance optimization in Fenrir with orjson for 7x faster JSON serialization, ObjectPool, ResponseCache, PerformanceMonitor, and optimize_app() for maximum throughput."},
    {"title": "Production Best Practices for Fenrir Python Applications", "id": "best-practices", "icon": "award", "description": "Production-ready patterns and best practices for Fenrir applications: performance optimization, security hardening, type hints, code organization, and deployment guidelines."},
    {"title": "Framework Comparison Fenrir vs FastAPI Flask Sanic", "id": "comparison", "icon": "bar-chart", "description": "Compare Fenrir framework vs Flask vs FastAPI vs Sanic vs Falcon vs Bottle features, performance benchmarks, ecosystem, use cases, and migration guides for informed decisions."},
    {"title": "Complete Conclusion and Fenrir v4.1.0 Release Changelog", "id": "conclusion", "icon": "flag", "description": "Fenrir v4.1.0 complete changelog with bug fixes, performance optimizations, test coverage improvements, benchmark results, and migration guide from previous versions."},
]

# Pre-compute sidebar index (dict lookup is O(1) vs list scan O(n))
_SIDEBAR_INDEX: Dict[str, int] = {item["id"]: i for i, item in enumerate(SIDEBAR)}
_SIDEBAR_IDS = frozenset(_SIDEBAR_INDEX.keys())

# ---------------------------------------------------------------------------
# Markdown (cached at module level)
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


def _render_markdown_raw(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """Render markdown file to HTML + TOC (uncached)."""
    filepath = os.path.join(CONTENT_DIR, f"{filename}.md")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None, None

    md = markdown.Markdown(extensions=_MD_EXTENSIONS)
    html_content = md.convert(content)

    # Add rel="noopener noreferrer" to external links
    html_content = _EXTERNAL_LINK_RE.sub(
        r'<a \1 rel="noopener noreferrer" target="_blank">', html_content
    )
    # Wrap tables for responsive CSS
    html_content = _TABLE_RE.sub(
        r'<div class="table-wrapper">\1</div>', html_content
    )

    return html_content, md.toc


@lru_cache(maxsize=128)
def _cached_render(filename: str, _mtime: float) -> Tuple[Optional[str], Optional[str]]:
    """LRU-cached markdown render (invalidated by mtime)."""
    return _render_markdown_raw(filename)


def cached_markdown(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """Get cached markdown HTML + TOC for a page."""
    filepath = os.path.join(CONTENT_DIR, f"{filename}.md")
    try:
        mtime = os.path.getmtime(filepath)
    except OSError:
        return None, None
    return _cached_render(filename, mtime)


# ---------------------------------------------------------------------------
# Search index (built once at startup)
# ---------------------------------------------------------------------------
_SEARCH_INDEX: Dict[str, Dict[str, str]] = {}


def _build_search_index() -> None:
    """Build search index from all documentation pages."""
    global _SEARCH_INDEX
    _SEARCH_INDEX.clear()
    for item in SIDEBAR:
        content_html, _ = cached_markdown(item["id"])
        if content_html is None:
            continue
        plain = html.unescape(_STRIP_HTML_RE.sub("", content_html))
        _SEARCH_INDEX[item["id"]] = {
            "title": item["title"].lower(),
            "text": plain.lower(),
        }


# ---------------------------------------------------------------------------
# Helpers (inlined for hot paths)
# ---------------------------------------------------------------------------
def _get_host() -> str:
    """Extract host from request (fast path)."""
    return request.host or request.headers.get("host", "localhost")


def _make_url(host: str, path: str) -> str:
    """Build canonical URL."""
    return f"https://{host}{path}"


# ---------------------------------------------------------------------------
# Listeners
# ---------------------------------------------------------------------------
_build_search_index()
logger.info("Search index built: %d pages", len(_SEARCH_INDEX))


@app.listener("before_server_start")
async def on_startup(app_instance: Any) -> None:
    logger.info("Starting Fenrir Docs server ...")


@app.listener("after_server_stop")
async def on_shutdown(app_instance: Any) -> None:
    logger.info("Fenrir Docs server stopped.")


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
@app.middleware("response")
async def add_security_headers(req: Any, resp: Any) -> None:
    resp.headers["X-Powered-By"] = "Fenrir Framework"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/static/<path:path>")
async def serve_static(path: str) -> Any:
    """Serve static files with long cache headers."""
    resp = send_from_directory(STATIC_DIR, path)
    # Add cache headers for static assets
    if hasattr(resp, "headers"):
        resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.get("/")
async def index() -> Any:
    return await doc("introduction")


@app.get("/docs/<doc_id>")
async def doc(doc_id: str) -> Any:
    content_html, toc_html = cached_markdown(doc_id)
    if content_html is None:
        raise HTTPNotFound(detail="Document not found")

    idx = _SIDEBAR_INDEX.get(doc_id, -1)
    prev_page = SIDEBAR[idx - 1] if idx > 0 else None
    next_page = SIDEBAR[idx + 1] if idx < len(SIDEBAR) - 1 else None
    current_page = SIDEBAR[idx] if idx != -1 else None

    # Get file modification time
    filepath = os.path.join(CONTENT_DIR, f"{doc_id}.md")
    try:
        mtime = os.path.getmtime(filepath)
        last_updated = datetime.datetime.fromtimestamp(mtime).strftime("%b %d, %Y")
        last_updated_iso = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except OSError:
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
# Search API
# ---------------------------------------------------------------------------
@app.get("/api/search")
async def search() -> Any:
    query = request.args.get("q", "").lower().strip()
    if not query or len(query) < 2:
        return JSONResponse([])

    results = []
    query_len = len(query)

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

            results.append({
                "title": item["title"],
                "id": item["id"],
                "snippet": snippet,
            })

    return JSONResponse(results)


# ---------------------------------------------------------------------------
# SEO endpoints
# ---------------------------------------------------------------------------
@app.get("/sitemap.xml")
async def sitemap() -> Any:
    host = _get_host()
    root_url = f"https://{host}/"
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
async def llms() -> Any:
    content = render_template("llms.txt")
    return Response(body=content, content_type="text/markdown; charset=utf-8")


@app.get("/robots.txt")
async def robots() -> Any:
    host = _get_host()
    root_url = f"https://{host}/"
    body = f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {root_url}sitemap.xml"
    return TextResponse(body)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.exception(404)
async def page_not_found(req: Any, exc: Any) -> Any:
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
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, app_path="app:app")
