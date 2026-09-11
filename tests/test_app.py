import json
import os
import sys
from unittest.mock import patch

import httpx
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


import app as docs_app
from app import (
    _SEARCH_INDEX,
    _SIDEBAR_INDEX,
    SIDEBAR,
    _get_host,
    _make_url,
    _render_markdown_raw,
    app,
    cached_markdown,
)


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestRoutes:
    async def test_index(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "Fenrir" in resp.text

    async def test_doc_valid_first_page(self, client):
        first = SIDEBAR[0]["id"]
        resp = await client.get(f"/docs/{first}")
        assert resp.status_code == 200

    async def test_doc_valid_last_page(self, client):
        last = SIDEBAR[-1]["id"]
        resp = await client.get(f"/docs/{last}")
        assert resp.status_code == 200

    async def test_doc_404(self, client):
        resp = await client.get("/docs/nonexistent-page")
        assert resp.status_code == 404
        assert "404" in resp.text

    async def test_static_css(self, client):
        resp = await client.get("/static/css/style.css")
        assert resp.status_code == 200
        assert resp.headers.get("cache-control") == "public, max-age=86400"

    async def test_static_404(self, client):
        resp = await client.get("/static/nonexistent.css")
        assert resp.status_code == 404

    async def test_search_with_results(self, client):
        resp = await client.get("/api/search?q=fenrir")
        assert resp.status_code == 200
        data = json.loads(resp.text)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]

    async def test_search_short_query(self, client):
        resp = await client.get("/api/search?q=x")
        assert resp.status_code == 200
        assert json.loads(resp.text) == []

    async def test_search_no_query(self, client):
        resp = await client.get("/api/search")
        assert resp.status_code == 200
        assert json.loads(resp.text) == []

    async def test_search_no_results(self, client):
        resp = await client.get("/api/search?q=zzzzzzz999")
        assert resp.status_code == 200
        assert json.loads(resp.text) == []

    async def test_sitemap_xml(self, client):
        resp = await client.get("/sitemap.xml")
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "application/xml"
        assert b"<urlset" in resp.content

    async def test_llms_txt(self, client):
        resp = await client.get("/llms.txt")
        assert resp.status_code == 200
        assert "Fenrir" in resp.text

    async def test_robots_txt(self, client):
        resp = await client.get("/robots.txt")
        assert resp.status_code == 200
        assert "User-agent" in resp.text

    async def test_playground(self, client):
        resp = await client.get("/playground")
        assert resp.status_code == 200
        assert "Playground" in resp.text
        assert "pyodide" in resp.text.lower() or "run" in resp.text.lower()

    async def test_health_check(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = json.loads(resp.text)
        assert data["status"] == "healthy"
        assert data["version"] == "4.4.0"
        assert data["pages"] == 43


class TestMiddleware:
    async def test_security_headers(self, client):
        resp = await client.get("/docs/introduction")
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


class TestFunctions:
    def test_get_host_with_context(self):
        ctx = app.test_request_context("/docs/introduction")
        with ctx:
            host = _get_host()
            assert isinstance(host, str)
            assert len(host) > 0

    def test_get_host_fallback(self):
        ctx = app.test_request_context("/")
        with ctx:
            docs_app.request._headers = {"host": "test.local"}
            host = _get_host()
            assert host == "test.local"

    def test_make_url(self):
        assert _make_url("example.com", "/docs/test") == "https://example.com/docs/test"
        assert _make_url("localhost:8000", "/") == "http://localhost:8000/"

    def test_cached_markdown_valid(self):
        html, _toc = cached_markdown("introduction")
        assert html is not None
        assert isinstance(html, str)
        assert len(html) > 0

    def test_cached_markdown_invalid(self):
        html, toc = cached_markdown("__nonexistent__")
        assert html is None
        assert toc is None

    def test_search_index_built(self):
        assert len(_SEARCH_INDEX) > 0
        for item in SIDEBAR:
            idx = _SEARCH_INDEX.get(item["id"])
            if idx is not None:
                assert "title" in idx
                assert "text" in idx

    def test_sidebar_index_complete(self):
        assert len(_SIDEBAR_INDEX) == len(SIDEBAR)
        for i, item in enumerate(SIDEBAR):
            assert _SIDEBAR_INDEX[item["id"]] == i

    def test_external_link_regex(self):
        html = '<a href="https://example.com">link</a>'
        result = docs_app._EXTERNAL_LINK_RE.sub(
            r'<a \1 rel="noopener noreferrer" target="_blank">', html
        )
        assert 'rel="noopener noreferrer"' in result
        assert 'target="_blank"' in result

    def test_table_wrapping_regex(self):
        html = '<table><tr><td>data</td></tr></table>'
        result = docs_app._TABLE_RE.sub(
            r'<div class="table-wrapper">\1</div>', html
        )
        assert '<div class="table-wrapper">' in result

    def test_strip_html_regex(self):
        assert docs_app._STRIP_HTML_RE.sub("", "<b>bold</b>") == "bold"
        assert docs_app._STRIP_HTML_RE.sub("", "no html") == "no html"

    def test_all_content_files_exist_in_sidebar(self):
        for item in SIDEBAR:
            filepath = os.path.join(docs_app.CONTENT_DIR, f"{item['id']}.md")
            assert os.path.exists(filepath), f"Missing content file: {item['id']}.md"

    def test_all_content_files_in_sidebar(self):
        content_dir = docs_app.CONTENT_DIR
        for fname in os.listdir(content_dir):
            if fname.endswith(".md"):
                doc_id = fname[:-3]
                assert doc_id in _SIDEBAR_INDEX, f"Missing sidebar entry: {doc_id}"


class TestDocNavigation:
    async def test_first_page_no_prev(self, client):
        first = SIDEBAR[0]["id"]
        resp = await client.get(f"/docs/{first}")
        assert resp.status_code == 200

    async def test_middle_page_nav(self, client):
        mid = SIDEBAR[len(SIDEBAR) // 2]["id"]
        resp = await client.get(f"/docs/{mid}")
        assert resp.status_code == 200

    async def test_last_page_no_next(self, client):
        last = SIDEBAR[-1]["id"]
        resp = await client.get(f"/docs/{last}")
        assert resp.status_code == 200


class TestEdgeCases:
    async def test_search_case_insensitive(self, client):
        resp = await client.get("/api/search?q=FENRIR")
        assert resp.status_code == 200
        data = json.loads(resp.text)
        assert len(data) > 0

    async def test_doc_path_traversal(self, client):
        resp = await client.get("/docs/../../../etc/passwd")
        assert resp.status_code == 404

    async def test_head_request(self, client):
        resp = await client.head("/")
        assert resp.status_code == 200

    async def test_options_request(self, client):
        resp = await client.options("/")
        assert resp.status_code == 204

    async def test_llms_has_all_docs(self, client):
        resp = await client.get("/llms.txt")
        text = resp.text
        for item in SIDEBAR:
            assert f"/docs/{item['id']}" in text, f"Missing in llms.txt: {item['id']}"

    async def test_sitemap_has_all_docs(self, client):
        resp = await client.get("/sitemap.xml")
        text = resp.text
        for item in SIDEBAR:
            assert f"docs/{item['id']}" in text, f"Missing in sitemap: {item['id']}"

    async def test_search_result_has_snippet(self, client):
        resp = await client.get("/api/search?q=introduction")
        assert resp.status_code == 200
        data = json.loads(resp.text)
        for result in data:
            assert "snippet" in result

    def test_cached_markdown_lru_cache(self):
        html1, _ = cached_markdown("introduction")
        html2, _ = cached_markdown("introduction")
        assert html1 == html2

    def test_render_markdown_raw_valid(self):
        html, _toc = _render_markdown_raw("introduction")
        assert html is not None
        assert isinstance(html, str)

    def test_render_markdown_raw_invalid(self):
        html, toc = _render_markdown_raw("__nonexistent__")
        assert html is None
        assert toc is None

    def test_listeners(self):
        import asyncio
        asyncio.run(docs_app.on_startup(None))
        asyncio.run(docs_app.on_shutdown(None))

    async def test_search_api_uses_orjson(self, client):
        resp = await client.get("/api/search?q=fenrir")
        assert resp.status_code == 200


class TestMissingCoverage:
    def test_import_orjson_success(self):
        """Test _import_orjson with orjson available"""
        result = docs_app._import_orjson()
        assert result is not None

    def test_import_orjson_import_error(self):
        """Test _import_orjson with ImportError"""
        import builtins
        original_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'orjson':
                raise ImportError("No module named 'orjson'")
            return original_import(name, *args, **kwargs)
        with patch.object(builtins, '__import__', side_effect=mock_import):
            result = docs_app._import_orjson()
            assert result is None

    def test_init_sentry_no_dsn(self):
        """Test _init_sentry when DSN is not set"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SENTRY_DSN", None)
            enabled, middleware = docs_app._init_sentry()
            assert enabled is False
            assert middleware is None

    def test_init_sentry_import_error(self):
        """Test _init_sentry with ImportError"""
        import builtins
        original_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'sentry_sdk':
                raise ImportError("No module named 'sentry_sdk'")
            return original_import(name, *args, **kwargs)
        with patch.dict(os.environ, {"SENTRY_DSN": "https://test@test.io/1"}), \
             patch.object(builtins, '__import__', side_effect=mock_import):
            enabled, _middleware = docs_app._init_sentry()
            assert enabled is False

    def test_init_sentry_general_error(self):
        """Test _init_sentry with ValueError"""
        with patch.dict(os.environ, {"SENTRY_DSN": "https://test@test.io/1"}), \
             patch('sentry_sdk.init', side_effect=ValueError("init failed")):
            enabled, _middleware = docs_app._init_sentry()
            assert enabled is False

    def test_init_fenrir_monitoring_error(self):
        """Test _init_fenrir_monitoring with ImportError"""
        import builtins
        original_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'fenrir.features':
                raise ImportError("No module")
            return original_import(name, *args, **kwargs)
        with patch.object(builtins, '__import__', side_effect=mock_import):
            docs_app._init_fenrir_monitoring()

    def test_build_search_index_skip_none(self):
        """Test _build_search_index skips pages with None content"""
        import copy
        original_index = copy.deepcopy(dict(docs_app._SEARCH_INDEX))
        try:
            with patch.object(docs_app, 'cached_markdown', return_value=(None, None)):
                docs_app._build_search_index()
                assert len(docs_app._SEARCH_INDEX) == 0
        finally:
            docs_app._SEARCH_INDEX.clear()
            docs_app._SEARCH_INDEX.update(original_index)

    async def test_doc_page_oserror(self, client):
        """Test OSError when getting file mtime (lines 343-345)"""
        import app as app_module
        original = app_module.os.path.getmtime
        content_dir = os.path.abspath(docs_app.CONTENT_DIR)
        call_count = [0]

        def selective_getmtime(path):
            abs_path = os.path.abspath(path)
            if abs_path.startswith(content_dir) and abs_path.endswith('.md'):
                call_count[0] += 1
                if call_count[0] == 1:
                    return original(path)
                raise OSError("simulated error")
            return original(path)

        app_module._cached_render.cache_clear()
        app_module.os.path.getmtime = selective_getmtime
        try:
            resp = await client.get("/docs/introduction")
            assert resp.status_code == 200
        finally:
            app_module.os.path.getmtime = original
            app_module._cached_render.cache_clear()

    async def test_search_skip_missing_index(self):
        """Test line 403: skip when idx_data is None"""
        import copy
        original_index = copy.deepcopy(dict(docs_app._SEARCH_INDEX))
        try:
            docs_app._SEARCH_INDEX.clear()
            transport = httpx.ASGITransport(app=docs_app.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.get("/api/search?q=test")
                assert resp.status_code == 200
                data = json.loads(resp.text)
                assert data == []
        finally:
            docs_app._SEARCH_INDEX.clear()
            docs_app._SEARCH_INDEX.update(original_index)

    async def test_search_no_orjson(self, client):
        """Test line 424: JSONResponse fallback when orjson is None"""
        import app as app_module
        original = app_module.orjson
        app_module.orjson = None
        try:
            resp = await client.get("/api/search?q=fenrir")
            assert resp.status_code == 200
            data = json.loads(resp.text)
            assert isinstance(data, list)
        finally:
            app_module.orjson = original

    async def test_doc_page_oserror_direct(self, client):
        """Test lines 343-345: OSError in doc handler - direct call"""
        import app as app_module
        original = app_module.os.path.getmtime
        content_dir = os.path.abspath(docs_app.CONTENT_DIR)
        call_count = [0]

        def selective_getmtime(path):
            abs_path = os.path.abspath(path)
            if abs_path.startswith(content_dir) and abs_path.endswith('.md'):
                call_count[0] += 1
                if call_count[0] == 1:
                    return original(path)
                raise OSError("simulated error")
            return original(path)

        app_module._cached_render.cache_clear()
        app_module.os.path.getmtime = selective_getmtime
        try:
            resp = await client.get("/docs/introduction")
            assert resp.status_code == 200
        finally:
            app_module.os.path.getmtime = original
            app_module._cached_render.cache_clear()


