import os
import re
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
    send_file,
)
from fenrir.features import init_fenrir_monitoring

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("docs-fenrir")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = Fenrir(title="Fenrir Docs", version="3.1.2")

# CORS – allow all origins for a public documentation site
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Monitoring Dashboard
init_fenrir_monitoring(app)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content")

# ---------------------------------------------------------------------------
# Sidebar (file-tree order)
# ---------------------------------------------------------------------------
SIDEBAR = [
    {"title": "Introduction to Fenrir", "id": "introduction", "icon": "info"},
    {"title": "Installation Guide", "id": "installation", "icon": "download"},
    {"title": "Project Structure", "id": "project-structure", "icon": "folder"},
    {"title": "Quick Start Guide", "id": "quick-start", "icon": "play"},
    {"title": "Basic Concepts", "id": "basic-concepts", "icon": "book-open"},
    {"title": "Routing System", "id": "routing", "icon": "git-commit"},
    {"title": "Request & Response", "id": "request-response", "icon": "arrow-left-right"},
    {"title": "Dependency Injection", "id": "dependency-injection", "icon": "plug"},
    {"title": "Data Validation", "id": "data-validation", "icon": "check-circle"},
    {"title": "Context Locals", "id": "context-locals", "icon": "database"},
    {"title": "Class-Based Resources", "id": "class-based-resources", "icon": "layers"},
    {"title": "File Upload", "id": "file-upload", "icon": "upload"},
    {"title": "WebSocket Support", "id": "websocket", "icon": "zap"},
    {"title": "Server-Sent Events (SSE)", "id": "server-sent-events", "icon": "radio"},
    {"title": "Jinja2 Templating", "id": "templating", "icon": "layout"},
    {"title": "Error Handling & Exceptions", "id": "error-handling", "icon": "alert-circle"},
    {"title": "Error Handling Compatibility", "id": "error-handling-compatibility", "icon": "shuffle"},
    {"title": "Middleware System", "id": "middleware", "icon": "cpu"},
    {"title": "Middleware Classes", "id": "middleware-classes", "icon": "layers"},
    {"title": "Sessions", "id": "sessions", "icon": "database"},
    {"title": "Pagination", "id": "pagination", "icon": "list"},
    {"title": "Background Tasks", "id": "background-tasks", "icon": "clock"},
    {"title": "Authentication & Security", "id": "authentication-security", "icon": "shield"},
    {"title": "Blueprints Organization", "id": "blueprints", "icon": "map"},
    {"title": "Application Configuration", "id": "configuration", "icon": "settings"},
    {"title": "Testing Guide", "id": "testing", "icon": "clipboard-list"},
    {"title": "CLI Tools Reference", "id": "cli-tools", "icon": "terminal"},
    {"title": "Advanced Features", "id": "advanced-features", "icon": "sliders"},
    {"title": "Monitoring Dashboard", "id": "monitoring", "icon": "activity"},
    {"title": "Signals System", "id": "signals", "icon": "radio"},
    {"title": "JSON Provider", "id": "json-provider", "icon": "braces"},
    {"title": "OpenAPI Customization", "id": "openapi-customization", "icon": "file-text"},
    {"title": "Best Practices", "id": "best-practices", "icon": "award"},
    {"title": "Framework Comparison", "id": "comparison", "icon": "bar-chart"},
    {"title": "Conclusion", "id": "conclusion", "icon": "flag"},
]

# Pre-build an id→index lookup for O(1) navigation
_SIDEBAR_INDEX = {item["id"]: i for i, item in enumerate(SIDEBAR)}

# ---------------------------------------------------------------------------
# Markdown renderer (cached per file)
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


def render_markdown(filename: str):
    """Render a Markdown file from the content directory to (html, toc)."""
    filepath = os.path.join(CONTENT_DIR, f"{filename}.md")
    if not os.path.exists(filepath):
        return None, None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    md = markdown.Markdown(extensions=_MD_EXTENSIONS)
    html = md.convert(content)

    # Add rel="noopener noreferrer" to external links
    html = _EXTERNAL_LINK_RE.sub(
        r'<a \1 rel="noopener noreferrer" target="_blank">', html
    )

    # Wrap tables in a scrollable container
    html = _TABLE_RE.sub(r'<div class="table-wrapper">\1</div>', html)

    return html, md.toc


def _markdown_cache_key(filename: str) -> str:
    filepath = os.path.join(CONTENT_DIR, f"{filename}.md")
    if not os.path.exists(filepath):
        return ""
    return str(os.path.getmtime(filepath))


@lru_cache(maxsize=64)
def _cached_render(filename: str, _mtime: str):
    """Lru-cached wrapper — invalidation via mtime key."""
    return render_markdown(filename)


def cached_markdown(filename: str):
    """Render Markdown with automatic cache based on file mtime."""
    mtime = _markdown_cache_key(filename)
    if not mtime:
        return None, None
    return _cached_render(filename, mtime)


# ---------------------------------------------------------------------------
# Listeners
# ---------------------------------------------------------------------------
@app.listener("before_server_start")
async def on_startup(app_instance):
    logger.info("Starting Fenrir Docs server …")


@app.listener("after_server_stop")
async def on_shutdown(app_instance):
    logger.info("Fenrir Docs server stopped.")

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
@app.middleware("request")
async def inject_request_meta(req):
    g.request_start = datetime.datetime.now()


@app.middleware("response")
async def add_server_header(req, resp):
    resp.headers["X-Powered-By"] = "Fenrir Framework"

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/static/<path:path>")
async def serve_static(path: str):
    filepath = os.path.join(BASE_DIR, "static", path)
    return send_file(filepath)


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
    query = request.args.get("q", "").lower().strip()
    if not query or len(query) < 2:
        return JSONResponse([])

    results = []
    for item in SIDEBAR:
        content_html, _ = cached_markdown(item["id"])
        if content_html is None:
            continue

        text_content = re.sub(r"<[^>]+>", "", content_html)

        if query in item["title"].lower() or query in text_content.lower():
            snippet = ""
            idx = text_content.lower().find(query)
            if idx != -1:
                start = max(0, idx - 40)
                end = min(len(text_content), idx + 60)
                snippet = "..." + text_content[start:end].strip() + "..."

            results.append({"title": item["title"], "id": item["id"], "snippet": snippet})

    return JSONResponse(results)

# ---------------------------------------------------------------------------
# SEO / Metadata endpoints
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
