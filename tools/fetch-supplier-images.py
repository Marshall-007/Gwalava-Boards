#!/usr/bin/env python3
"""Pull the supplier decor images onto this site instead of hotlinking them.

Right now the product and project pages load 40-odd decor photos straight from
pgbison.co.za. That works until the supplier renames a file or blocks
hotlinking, at which point the products page fills up with broken images. This
script copies them into img/decors/ and points the HTML at the local files.

    python3 tools/fetch-supplier-images.py
        Find every remote image the site references, download the ones that are
        missing, then rewrite the pages to use the local copies.

    python3 tools/fetch-supplier-images.py --dry-run
        Show what would happen without writing anything.

    python3 tools/fetch-supplier-images.py --no-rewrite
        Download only, leave the HTML alone.

    python3 tools/fetch-supplier-images.py --from-page URL [--dest NAME]
        Scrape one supplier page (a Sonae Arauco decor range, a PG Bison
        collection) and download every image it shows into
        img/decors/NAME/. Nothing is rewritten - these are new images for you
        to place on a page yourself, and the script prints the paths so you can
        paste them into tools/gallery-manifest.tsv or products.html.

Standard library only, so there is nothing to install.

A note on where the images come from: decor photographs belong to the board
manufacturer. Showing them as a supplier's product range - which is what this
site does - is normal practice, but keep the decor name with each image and do
not present them as photographs of your own installations.
"""

import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECOR_DIR = ROOT / "img" / "decors"
PAGES = sorted(ROOT.glob("*.html"))

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")
REMOTE_IMAGE = re.compile(r'https?://[^"\'\s>]+?\.(?:jpg|jpeg|png|webp|gif|avif)', re.I)
USER_AGENT = "Mozilla/5.0 (compatible; GwalavaBoards-site-build/1.0)"
TIMEOUT = 30


def local_name(url):
    """img/decors/<host>/<file name> for a given remote URL."""
    parts = urllib.parse.urlsplit(url)
    host = re.sub(r"[^A-Za-z0-9._-]", "-", parts.netloc.replace("www.", "").split(":")[0])
    name = urllib.parse.unquote(Path(parts.path).name)
    name = re.sub(r"[^A-Za-z0-9._-]", "-", name)
    return Path(host) / name


def download(url, target, dry_run):
    if target.exists():
        return "have"
    if dry_run:
        return "would download"
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as err:
        return "FAILED (%s)" % err
    if not body:
        return "FAILED (empty response)"
    target.write_bytes(body)
    size = "%d KB" % (len(body) // 1024) if len(body) >= 1024 else "%d bytes" % len(body)
    return "downloaded (%s)" % size


def find_remote_images():
    """Every remote image URL the site references, with the pages using it."""
    found = {}
    for page in PAGES:
        for url in REMOTE_IMAGE.findall(page.read_text(encoding="utf-8")):
            found.setdefault(url, set()).add(page.name)
    return dict(sorted(found.items()))


def mirror_site_images(args):
    images = find_remote_images()
    if not images:
        print("No remote images referenced - the site is already fully local.")
        return 0

    print("%d remote images referenced across %d pages\n" % (len(images), len(PAGES)))
    failures = 0
    mapping = {}
    for url, pages in images.items():
        target = DECOR_DIR / local_name(url)
        result = download(url, target, args.dry_run)
        if result.startswith("FAILED"):
            failures += 1
        else:
            mapping[url] = target.relative_to(ROOT).as_posix()
        print("  %-12s %s" % (result.split(" (")[0], target.relative_to(ROOT)))
        if result.startswith("FAILED"):
            print("               %s  (used on %s)" % (result, ", ".join(sorted(pages))))

    if failures:
        print("\n%d image(s) could not be fetched. Those pages keep their current remote"
              "\nURLs, so nothing breaks - re-run the script to try them again." % failures)

    if args.no_rewrite or args.dry_run:
        print("\nHTML not rewritten.")
        return 1 if failures else 0

    rewritten = 0
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        original = text
        for url, local in mapping.items():
            text = text.replace(url, local)
        if text != original:
            page.write_text(text, encoding="utf-8")
            rewritten += 1
            print("rewrote %s" % page.name)
    print("\n%d page(s) now point at local copies in img/decors/." % rewritten)
    return 1 if failures else 0


def scrape_page(args):
    dest = args.dest or urllib.parse.urlsplit(args.from_page).netloc.replace("www.", "")
    request = urllib.request.Request(args.from_page, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            html = response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as err:
        sys.exit("Could not open %s: %s" % (args.from_page, err))

    candidates = set()
    # src / data-src / href attributes and every entry of a srcset
    for match in re.findall(r'(?:src|data-src|data-lazy-src|href)="([^"]+)"', html, re.I):
        candidates.add(match)
    for srcset in re.findall(r'srcset="([^"]+)"', html, re.I):
        for part in srcset.split(","):
            candidates.add(part.strip().split(" ")[0])
    for match in re.findall(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html, re.I):
        candidates.add(match)

    urls = sorted(
        urllib.parse.urljoin(args.from_page, c)
        for c in candidates
        if c and Path(urllib.parse.urlsplit(c).path).suffix.lower() in IMAGE_SUFFIXES
    )
    if not urls:
        print("No images found on that page. It may build its gallery with JavaScript;"
              "\nin that case open the page, right-click the images you want and save them"
              "\ninto img/decors/%s/ by hand." % dest)
        return 0

    print("%d image(s) found on %s\n" % (len(urls), args.from_page))
    saved = []
    for url in urls:
        target = DECOR_DIR / dest / local_name(url).name
        result = download(url, target, args.dry_run)
        print("  %-12s %s" % (result.split(" (")[0], target.relative_to(ROOT)))
        if not result.startswith("FAILED"):
            saved.append(target.relative_to(ROOT).as_posix())

    if saved and not args.dry_run:
        print("\nSaved into img/decors/%s/. To show any of them in the gallery, add a row to"
              "\ntools/gallery-manifest.tsv and run python3 tools/build-gallery.py:\n" % dest)
        for path in saved[:5]:
            print("    kitchens\tsome-slug\tSome Title\t%s" % path)
        if len(saved) > 5:
            print("    ... and %d more" % (len(saved) - 5))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    parser.add_argument("--no-rewrite", action="store_true", help="download but leave the HTML pointing at the supplier")
    parser.add_argument("--from-page", metavar="URL", help="scrape one supplier page for images")
    parser.add_argument("--dest", metavar="NAME", help="subfolder under img/decors for --from-page (default: the host name)")
    args = parser.parse_args()

    if args.from_page:
        return scrape_page(args)
    return mirror_site_images(args)


if __name__ == "__main__":
    sys.exit(main())
