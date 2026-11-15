#!/usr/bin/env python3
"""Export a portable multi-page preview, without publishing or building Jekyll."""

import argparse
import base64
import mimetypes
import posixpath
import re
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from preview import ROOT, discover_pages, render_page


def output_name(route):
    return PurePosixPath(route.lstrip("/")) / "index.html"


def image_data_url(path):
    image = path.read_bytes()
    if image.startswith(b"\xff\xd8\xff"):
        image_type = "image/jpeg"
    elif image.startswith(b"\x89PNG\r\n\x1a\n"):
        image_type = "image/png"
    else:
        image_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return f"data:{image_type};base64,{base64.b64encode(image).decode('ascii')}"


def export_preview(destination):
    pages = discover_pages()
    css = (ROOT / "assets/css/home.css").read_text("utf-8").replace("</style", "<\\/style")
    javascript = (ROOT / "assets/js/home.js").read_text("utf-8").replace("</script", "<\\/script")
    portrait = image_data_url(ROOT / "images/profile.png")
    for route in pages:
        html = render_page(route).decode("utf-8")
        html = html.replace('<link rel="stylesheet" href="/assets/css/home.css">',
                            f"<style>\n{css}\n</style>")
        html = html.replace('<script src="/assets/js/home.js" defer></script>',
                            f"<script>\n{javascript}\n</script>")
        html = html.replace('src="/images/profile.png"', f'src="{portrait}"')
        current = output_name(route)

        def local_link(match):
            quote, href = match.groups()
            link = urlsplit(href)
            if link.netloc:
                return match.group(0)
            target = link.path
            if target not in pages and target + "/" in pages:
                target += "/"
            if target in {"/about/", "/about.html"}:
                target = "/"
            if target not in pages:
                return match.group(0)
            relative = posixpath.relpath(str(output_name(target)), str(current.parent))
            if link.query:
                relative += "?" + link.query
            if link.fragment:
                relative += "#" + link.fragment
            return f"href={quote}{relative}{quote}"

        html = re.sub(r"href=([\"'])(/[^\"']*)\1", local_link, html)
        output_path = destination / str(current)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
    return len(pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="Destination preview directory")
    args = parser.parse_args()
    destination = args.destination.expanduser().resolve()
    count = export_preview(destination)
    print(f"Portable preview: {destination / 'index.html'} ({count} pages)")


if __name__ == "__main__":
    main()
