# Gwalava Boards

The website for **Gwalava Boards and Furniture Fittings** - melamine board cutting,
edge banding and carpentry in Eldorado Park, Johannesburg.

It is a plain static site: HTML, CSS and a little JavaScript. There is no build
step to run before deploying and no server-side code. Open `index.html` in a
browser and it works.

---

## Contents

- [Pages](#pages)
- [Running it locally](#running-it-locally)
- [The enquiry form](#the-enquiry-form)
- [The gallery](#the-gallery)
- [Supplier decor images](#supplier-decor-images)
- [Layout of the repository](#layout-of-the-repository)
- [Deploying](#deploying)
- [Credits](#credits)

---

## Pages

| Page | What it is |
| --- | --- |
| `index.html` | Home |
| `about.html` | About the business and the team |
| `service.html` | Board cutting, edging and carpentry services |
| `products.html` | Board decors, colours, worktops and edging |
| `gallery.html` | Filterable photo gallery with a lightbox |
| `project.html` | Recent projects |
| `faq.html` | Frequently asked questions |
| `contact.html` | Contact details, map and the enquiry form |
| `thank-you.html` | Shown after a form submit when JavaScript is off |
| `team.html`, `testimonial.html`, `feature.html` | Extra pages, not in the main menu |
| `404.html` | Shown by the host for an unknown URL |

---

## Running it locally

Any static file server will do. The simplest:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

Opening the files directly with `file://` mostly works, but a server is closer
to the real thing.

---

## The enquiry form

The form on `contact.html` is handled by [FormSubmit](https://formsubmit.co) -
a free service that emails form submissions, so the site does not need a
backend.

How it is wired up:

- The form posts to `https://formsubmit.co/marshalldube9@gmail.com`, with a
  copy to `gwalava@gmail.com` via the `_cc` field.
- `js/contact-form.js` intercepts the submit and sends it in the background to
  the `/ajax/` variant of that URL, so the visitor stays on the page. FormSubmit
  only sends CORS headers from the `/ajax/` endpoint - posting to the plain URL
  with `fetch` fails in the browser even when the mail goes through.
- `_captcha` is `false`. FormSubmit rejects background submissions while its
  captcha is on. The hidden `_honey` field catches bots instead.
- With JavaScript off the form posts normally and FormSubmit redirects to
  `thank-you.html`, named in the `_next` field. That field needs an absolute
  URL, so **update it if the site moves to a custom domain**.

**First-time setup:** FormSubmit emails the recipient address a confirmation
link the first time a form is submitted, and sends nothing until that link is
clicked. If enquiries are not arriving, check that inbox (and its spam folder)
for the activation mail. The confirmation message from FormSubmit is shown to
the visitor, so a stuck activation is visible rather than silent.

To change where enquiries go, edit the `action` and the `_cc` field in
`contact.html` - nothing else needs to change.

---

## The gallery

`gallery.html` filters by category and opens photos in a lightbox with keyboard
arrows, Escape to close and swipe support on phones. Linking to
`gallery.html#kitchens` opens the page with that filter already applied.

The grid is generated, not hand written. To change what appears:

1. Edit `tools/gallery-manifest.tsv` - one tab separated row per photo:

   ```
   category<TAB>slug<TAB>title<TAB>source image path
   ```

   `category` is one of `kitchens`, `wardrobes`, `furniture`, `workshop`.

2. Rebuild:

   ```bash
   pip install Pillow          # once
   python3 tools/build-gallery.py
   ```

That writes a grid thumbnail to `img/gallery/thumbs/` and a lightbox-sized copy
to `img/gallery/web/`, rewrites the grid inside `gallery.html`, and deletes
derivatives whose row you removed. Original photos are never modified.

This matters for page weight: several workshop photos are 5-6MB straight off a
phone. The page only ever loads the generated copies. The script also bakes in
EXIF rotation, without which those phone photos display on their side.

---

## Supplier decor images

The products and projects pages currently load around 40 decor photos directly
from `pgbison.co.za`. That works, but it breaks the moment the supplier renames
a file or blocks hotlinking, and every visitor waits on their server.

`tools/fetch-supplier-images.py` copies them onto this site:

```bash
python3 tools/fetch-supplier-images.py --dry-run   # see what it would fetch
python3 tools/fetch-supplier-images.py             # download, then update the HTML
```

It finds every remote image the site references, saves it under `img/decors/`,
and repoints the pages at the local copies. Anything it cannot fetch keeps its
current remote URL, so a partial run never breaks a page.

To pull images from a supplier page that the site does not reference yet - a
Sonae Arauco decor range, a new PG Bison collection:

```bash
python3 tools/fetch-supplier-images.py --from-page "https://example.com/decors" --dest sonae
```

Those land in `img/decors/sonae/` for you to place on a page or add to the
gallery manifest.

Standard library only - nothing to install.

**On using them:** decor photographs belong to the board manufacturer. Showing
them as the product range a supplier stocks is normal practice, but keep the
decor name with each image and do not present manufacturer photography as
pictures of your own installations.

---

## Layout of the repository

```
├── *.html                  the pages
├── css/
│   ├── bootstrap.min.css   Bootstrap 5
│   └── style.css           site styles, including the gallery and lightbox
├── js/
│   ├── main.js             spinner, sticky nav, carousels, counters
│   ├── contact-form.js     enquiry form submission
│   └── gallery.js          gallery filtering and lightbox
├── img/
│   ├── gallery/thumbs/     generated grid thumbnails
│   ├── gallery/web/        generated lightbox images
│   ├── decors/             supplier images, once downloaded
│   └── ...                 source photographs
├── lib/                    WOW, Owl Carousel, Waypoints, CounterUp, Easing
├── scss/                   Bootstrap source, not used at runtime
└── tools/
    ├── gallery-manifest.tsv
    ├── build-gallery.py
    └── fetch-supplier-images.py
```

Bootstrap's JavaScript, jQuery, Font Awesome and Google Fonts load from CDNs.
If a CDN is unreachable the page still renders and stays readable - the loading
spinner is dismissed by plain JavaScript that does not wait for jQuery.

---

## Deploying

The site is served straight from this repository, so deploying is a push to the
default branch. Nothing needs to be built first.

If you add photos, run `python3 tools/build-gallery.py` and commit the generated
files in `img/gallery/thumbs/` and `img/gallery/web/` along with the originals.

---

## Credits

Built on the *Industro* template by [HTML Codex](https://htmlcodex.com),
substantially reworked for Gwalava Boards. See `LICENSE.txt` for the template
licence.
