#!/usr/bin/env python3
"""Preview the site's HTML pages locally without installing Jekyll."""

import argparse
import html
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIRECTORIES = {"assets", "images", "files"}
ASSET_EXTENSIONS = {
    ".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif",
    ".svg", ".ico", ".pdf", ".woff", ".woff2", ".ttf", ".otf",
    ".json", ".webmanifest",
}
ALIASES = {"/about/": "/", "/about.html": "/"}
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def split_frontmatter(source):
    match = FRONTMATTER.match(source)
    if not match:
        return {}, source
    metadata = {}
    for line in match.group(1).splitlines():
        field = re.match(r"^([A-Za-z_]\w*):\s*(.*?)\s*$", line)
        if field:
            key, value = field.groups()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            metadata[key] = value
    return metadata, source[match.end():]


def discover_pages():
    pages = {}
    for path in sorted((ROOT / "_pages").iterdir()):
        if path.is_file() and path.suffix in {".md", ".html"}:
            metadata, body = split_frontmatter(path.read_text("utf-8"))
            route = metadata.get("permalink", "")
            if route.startswith("/"):
                pages[route] = (metadata, body)
    return pages


def render_page(route="/"):
    route = ALIASES.get(route, route)
    page = discover_pages().get(route)
    if page is None:
        raise FileNotFoundError(f"No page for {route}")
    metadata, content = page
    _, layout = split_frontmatter((ROOT / "_layouts/home.html").read_text("utf-8"))
    rendered = layout.replace("{{ content }}", content)
    for key in ("title", "section"):
        rendered = re.sub(r"\{\{\s*page\." + key + r"\s*\}\}",
                          lambda match: html.escape(metadata.get(key, ""), quote=True), rendered)
    rendered = re.sub(r"\{\{\s*(['\"])(.*?)\1\s*\|\s*relative_url\s*\}\}",
                      lambda match: match.group(2), rendered)
    return rendered.encode("utf-8")


def render_homepage():
    return render_page("/")


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def send_head(self):
        request = urlsplit(self.path)
        path = unquote(request.path)
        try:
            pages = discover_pages()
            if path not in pages and path + "/" in pages:
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                self.send_header("Location", path + "/" + ("?" + request.query if request.query else ""))
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
            if path in pages or path in ALIASES:
                body = render_page(path)
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                return BytesIO(body)
        except (OSError, UnicodeError):
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Page cannot be read")
            return None
        parts = path.lstrip("/").split("/")
        if (not parts or parts[0] not in ASSET_DIRECTORIES or "\\" in path
                or any(not part or part.startswith((".", "_")) for part in parts)):
            self.send_error(HTTPStatus.NOT_FOUND)
            return None
        asset = (ROOT / path.lstrip("/")).resolve()
        if (not asset.is_relative_to(ROOT) or not asset.is_file()
                or asset.suffix.lower() not in ASSET_EXTENSIONS):
            self.send_error(HTTPStatus.NOT_FOUND)
            return None
        return super().send_head()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=4173, help="Port (default: 4173)")
    args = parser.parse_args()
    try:
        server = ThreadingHTTPServer((args.host, args.port), PreviewHandler)
    except OSError as error:
        parser.exit(1, f"Could not start local preview: {error}\n")
    address = "localhost" if args.host in {"0.0.0.0", "::"} else args.host
    print(f"Local: http://{address}:{server.server_port}/", flush=True)
    print("Refresh your browser after edits. Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
