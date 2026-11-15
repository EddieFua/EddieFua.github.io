# Local website preview

From the repository folder, run:

```sh
python3 tools/preview.py
```

Open **http://127.0.0.1:4173/**. The homepage, publications, experience, and contact pages are separate pages with working navigation. The server rereads source files on each request; refresh your browser after edits. Stop the preview with `Ctrl+C`.

Use `--port 4174` to choose another port, or `--host` to change the bind address. The default address keeps the preview on your computer.

To create a portable preview that you can keep and open without a running server:

```sh
python3 tools/export_preview.py /absolute/path/to/preview-folder
```

Open the exported `index.html` in a browser. Navigation uses relative file links, and each page embeds its styles, scripts, and profile photograph. External publication and academic profile links retain their original destinations.

These dependency-free previews support the site's HTML pages, basic page metadata, and `relative_url` references. They are conveniences for visual review, not full Jekyll builds: they do not run Jekyll plugins or convert Markdown.

For the production build, use the repository's Jekyll environment:

```sh
bundle install
bundle exec jekyll build
```

Neither preview tool publishes or pushes to GitHub. The local server exposes only rendered pages and supported files in `assets/`, `images/`, and `files/`; repository internals and directory listings are unavailable.
