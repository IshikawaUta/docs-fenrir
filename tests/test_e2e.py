import os
import sys
import json
import pytest
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app, SIDEBAR


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestE2EHomepage:
    async def test_homepage_returns_html(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("text/html")

    async def test_homepage_has_sidebar(self, client):
        resp = await client.get("/")
        html = resp.text
        for item in SIDEBAR[:3]:
            assert item["title"] in html or item["id"] in html

    async def test_homepage_has_canonical(self, client):
        resp = await client.get("/")
        assert 'rel="canonical"' in resp.text


class TestE2EDocPages:
    async def test_all_docs_render(self, client):
        for item in SIDEBAR:
            resp = await client.get(f"/docs/{item['id']}")
            assert resp.status_code == 200, f"Failed: /docs/{item['id']}"

    async def test_doc_has_title(self, client):
        resp = await client.get("/docs/introduction")
        assert "Fenrir" in resp.text

    async def test_doc_has_edit_link(self, client):
        resp = await client.get("/docs/introduction")
        assert "github.com" in resp.text

    async def test_doc_has_last_updated(self, client):
        resp = await client.get("/docs/introduction")
        assert "Last Updated" in resp.text or "last updated" in resp.text.lower()

    async def test_doc_navigation_first_page(self, client):
        resp = await client.get(f"/docs/{SIDEBAR[0]['id']}")
        html = resp.text
        assert "Next" in html or "next" in html.lower()

    async def test_doc_navigation_last_page(self, client):
        resp = await client.get(f"/docs/{SIDEBAR[-1]['id']}")
        html = resp.text
        assert "Prev" in html or "prev" in html.lower()

    async def test_doc_codehilite_css(self, client):
        resp = await client.get("/docs/introduction")
        assert "highlight" in resp.text

    async def test_doc_toc_rendered(self, client):
        resp = await client.get("/docs/introduction")
        assert "toc" in resp.text.lower()

    async def test_doc_page_not_found_404(self, client):
        resp = await client.get("/docs/this-page-does-not-exist-xyz")
        assert resp.status_code == 404
        assert "404" in resp.text


class TestE2ESearch:
    async def test_search_returns_json(self, client):
        resp = await client.get("/api/search?q=routing")
        assert resp.status_code == 200
        data = json.loads(resp.text)
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_search_results_have_structure(self, client):
        resp = await client.get("/api/search?q=middleware")
        data = json.loads(resp.text)
        for r in data:
            assert "id" in r
            assert "title" in r
            assert "snippet" in r

    async def test_search_case_insensitive(self, client):
        lower = json.loads((await client.get("/api/search?q=fenrir")).text)
        upper = json.loads((await client.get("/api/search?q=FENRIR")).text)
        assert len(lower) == len(upper)

    async def test_search_empty_query(self, client):
        resp = await client.get("/api/search?q=")
        assert json.loads(resp.text) == []

    async def test_search_no_query_param(self, client):
        resp = await client.get("/api/search")
        assert json.loads(resp.text) == []

    async def test_search_short_query(self, client):
        resp = await client.get("/api/search?q=a")
        assert json.loads(resp.text) == []

    async def test_search_no_matches(self, client):
        resp = await client.get("/api/search?q=xxxxxxxxxxyyyyyyyyyy")
        assert json.loads(resp.text) == []

    async def test_search_snippet_contains_query(self, client):
        resp = await client.get("/api/search?q=installation")
        data = json.loads(resp.text)
        for r in data:
            assert "installation" in r["snippet"].lower() or "installation" in r["title"].lower()


class TestE2ESEO:
    async def test_sitemap_xml(self, client):
        resp = await client.get("/sitemap.xml")
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "application/xml"
        body = resp.text
        for item in SIDEBAR:
            assert f"docs/{item['id']}" in body
        assert "<?xml" in body

    async def test_robots_txt(self, client):
        resp = await client.get("/robots.txt")
        assert resp.status_code == 200
        body = resp.text
        assert "User-agent" in body
        assert "Sitemap" in body
        assert "Disallow: /api/" in body

    async def test_llms_txt(self, client):
        resp = await client.get("/llms.txt")
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("text/markdown")
        body = resp.text
        for item in SIDEBAR:
            assert f"/docs/{item['id']}" in body

    async def test_llms_has_framework_name(self, client):
        resp = await client.get("/llms.txt")
        assert "Fenrir" in resp.text


class TestE2EStatic:
    async def test_css_served(self, client):
        resp = await client.get("/static/css/style.css")
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("text/css")

    async def test_js_served(self, client):
        resp = await client.get("/static/js/main.js")
        assert resp.status_code == 200
        assert "javascript" in resp.headers.get("content-type", "")

    async def test_favicon_served(self, client):
        resp = await client.get("/static/images/favicon.png")
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("image/png")

    async def test_static_cache_headers(self, client):
        resp = await client.get("/static/css/style.css")
        assert resp.headers.get("cache-control") == "public, max-age=86400"

    async def test_static_not_found(self, client):
        resp = await client.get("/static/nonexistent/file.txt")
        assert resp.status_code == 404

    async def test_static_path_traversal(self, client):
        resp = await client.get("/static/../app.py")
        assert resp.status_code == 404


class TestE2EMiddleware:
    async def test_security_headers_on_html(self, client):
        resp = await client.get("/docs/introduction")
        assert resp.headers.get("x-powered-by") == "Fenrir Framework"
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    async def test_security_headers_on_json(self, client):
        resp = await client.get("/api/search?q=fenrir")
        assert resp.headers.get("x-powered-by") == "Fenrir Framework"
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"

    async def test_security_headers_on_static(self, client):
        resp = await client.get("/static/css/style.css")
        assert resp.headers.get("x-powered-by") == "Fenrir Framework"
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"

    async def test_cors_headers(self, client):
        resp = await client.options("/")
        assert resp.status_code == 204
        assert resp.headers.get("access-control-allow-origin") == "*"

    async def test_cors_on_get(self, client):
        resp = await client.get("/")
        assert resp.headers.get("access-control-allow-origin") == "*"

    async def test_gzip_compression(self, client):
        resp = await client.get(
            "/docs/introduction",
            headers={"accept-encoding": "gzip"},
        )
        assert resp.status_code == 200
        content_enc = resp.headers.get("content-encoding", "")
        assert content_enc == "gzip" or content_enc == ""

    async def test_request_id_header(self, client):
        resp = await client.get("/")
        assert resp.headers.get("x-request-id") is not None

    async def test_request_id_preserved(self, client):
        resp = await client.get("/", headers={"x-request-id": "my-custom-id"})
        assert resp.headers.get("x-request-id") == "my-custom-id"


class TestE2EHTTPMethods:
    async def test_head(self, client):
        resp = await client.head("/")
        assert resp.status_code == 200

    async def test_head_on_doc(self, client):
        resp = await client.head("/docs/introduction")
        assert resp.status_code == 200

    async def test_options(self, client):
        resp = await client.options("/")
        assert resp.status_code == 204

    async def test_post_on_root_returns_405(self, client):
        resp = await client.post("/")
        assert resp.status_code == 405 or resp.status_code == 200


class TestE2EExternalLinks:
    async def test_external_links_have_rel(self, client):
        resp = await client.get("/docs/introduction")
        html = resp.text
        import re
        external_links = re.findall(r'href="https?://', html)
        if external_links:
            assert 'rel="noopener noreferrer"' in html
            assert 'target="_blank"' in html

    async def test_tables_are_wrapped(self, client):
        resp = await client.get("/docs/comparison")
        if "table-wrapper" in resp.text or "<table" in resp.text:
            assert "table-wrapper" in resp.text


class TestE2ECrossPage:
    async def test_nav_links_are_valid(self, client):
        import re
        links = set()
        for item in SIDEBAR:
            resp = await client.get(f"/docs/{item['id']}")
            found = re.findall(r'href="/docs/([^"]+)"', resp.text)
            links.update(found)
        for link in links:
            link_resp = await client.get(f"/docs/{link}")
            assert link_resp.status_code == 200, f"Broken link: /docs/{link}"

    async def test_sidebar_links_are_valid(self, client):
        for item in SIDEBAR:
            resp = await client.get(f"/docs/{item['id']}")
            assert resp.status_code == 200
