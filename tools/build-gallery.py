#!/usr/bin/env python3
"""Generate the gallery images and the gallery.html grid from the manifest.

Reads tools/gallery-manifest.tsv and for every row writes two derivatives:

    img/gallery/thumbs/<slug>.jpg   grid tile, 800px wide
    img/gallery/web/<slug>.jpg      lightbox copy, 1600px wide

Neither is ever upscaled past the source, and the source images themselves are
left untouched. Several of the workshop photos come straight off a phone at
5-6MB each, which is far too heavy to put in a grid, so the page only ever
loads the derivatives.

The grid markup is then written into gallery.html between the
GALLERY:START / GALLERY:END markers, so re-running after editing the manifest
keeps the page in step with it.

Usage:
    python3 tools/build-gallery.py            # build everything
    python3 tools/build-gallery.py --force    # rebuild images that already exist

Requires Pillow:  pip install Pillow
"""

import html
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "gallery-manifest.tsv"
PAGE = ROOT / "gallery.html"
THUMB_DIR = ROOT / "img" / "gallery" / "thumbs"
WEB_DIR = ROOT / "img" / "gallery" / "web"

THUMB_WIDTH = 800
WEB_WIDTH = 1600
THUMB_QUALITY = 78
WEB_QUALITY = 82

START = "<!-- GALLERY:START -->"
END = "<!-- GALLERY:END -->"


def read_manifest():
    rows = []
    seen = set()
    for number, line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 4:
            sys.exit("%s:%d: expected 4 tab separated fields, got %d" % (MANIFEST.name, number, len(parts)))
        category, slug, title, source = (p.strip() for p in parts)
        if slug in seen:
            sys.exit("%s:%d: duplicate slug %r" % (MANIFEST.name, number, slug))
        seen.add(slug)
        path = ROOT / source
        if not path.is_file():
            sys.exit("%s:%d: missing source image %s" % (MANIFEST.name, number, source))
        rows.append({"category": category, "slug": slug, "title": title, "source": path})
    return rows


def derive(source, target, width, quality, force):
    """Write a downscaled copy and return (size, was_written)."""
    if target.exists() and not force:
        with Image.open(target) as existing:
            return existing.size, False
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as im:
        # Phone photos record their rotation in EXIF rather than in the pixels.
        # Resizing throws that tag away, so bake the rotation in first or the
        # workshop shots come out on their side.
        im = ImageOps.exif_transpose(im).convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(target, "JPEG", quality=quality, optimize=True, progressive=True)
        return im.size, True


def tile(row, index):
    """One grid tile. The first few load eagerly so the page has something
    on screen immediately; the rest wait until they are scrolled to."""
    title = html.escape(row["title"], quote=True)
    loading = "eager" if index < 8 else "lazy"
    return """                <div class="col-lg-4 col-md-6 gallery-col" data-category="{category}">
                    <a class="gallery-item" href="img/gallery/web/{slug}.jpg" data-title="{title}">
                        <img src="img/gallery/thumbs/{slug}.jpg" alt="{title}" loading="{loading}" width="{width}" height="{height}">
                        <div class="gallery-overlay">
                            <span class="gallery-zoom"><i class="fa fa-search-plus"></i></span>
                            <h6 class="gallery-caption">{title}</h6>
                        </div>
                    </a>
                </div>""".format(
        category=row["category"],
        slug=row["slug"],
        title=title,
        loading=loading,
        width=row["thumb_size"][0],
        height=row["thumb_size"][1],
    )


def main():
    force = "--force" in sys.argv[1:]
    rows = read_manifest()

    built = 0
    for row in rows:
        row["thumb_size"], wrote = derive(
            row["source"], THUMB_DIR / (row["slug"] + ".jpg"), THUMB_WIDTH, THUMB_QUALITY, force
        )
        built += wrote
        _, wrote = derive(row["source"], WEB_DIR / (row["slug"] + ".jpg"), WEB_WIDTH, WEB_QUALITY, force)
        built += wrote
    # Drop derivatives whose row has been taken out of the manifest.
    wanted = {row["slug"] + ".jpg" for row in rows}
    pruned = 0
    for folder in (THUMB_DIR, WEB_DIR):
        for stale in folder.glob("*.jpg"):
            if stale.name not in wanted:
                stale.unlink()
                pruned += 1

    print("%d photos in the manifest, %d derivative files written, %d pruned"
          % (len(rows), built, pruned))

    if not PAGE.exists():
        print("gallery.html not found, skipped the markup step")
        return

    page = PAGE.read_text(encoding="utf-8")
    if START not in page or END not in page:
        sys.exit("gallery.html is missing the %s / %s markers" % (START, END))

    grid = "\n".join(tile(row, i) for i, row in enumerate(rows))
    head, rest = page.split(START, 1)
    _, tail = rest.split(END, 1)
    PAGE.write_text(head + START + "\n" + grid + "\n" + " " * 16 + END + tail, encoding="utf-8")

    counts = {}
    for row in rows:
        counts[row["category"]] = counts.get(row["category"], 0) + 1
    print("gallery.html grid updated: " + ", ".join("%s %d" % kv for kv in sorted(counts.items())))


if __name__ == "__main__":
    main()
