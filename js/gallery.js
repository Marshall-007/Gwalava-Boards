/**
 * Gallery filtering and lightbox.
 *
 * The grid is plain markup, so the page still shows every photo with the
 * script disabled - the filter bar and the lightbox are enhancements on top.
 * Navigation stays inside whatever the active filter is showing, so paging
 * through "Kitchens" never jumps into a workshop photo.
 */
(function () {
    "use strict";

    var grid = document.querySelector("[data-gallery]");
    if (!grid) {
        return;
    }

    var items = Array.prototype.slice.call(grid.querySelectorAll(".gallery-item"));
    var filters = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));
    var empty = document.querySelector("[data-gallery-empty]");
    var current = -1;

    /* ---------------------------------------------------------------- filters */

    function visibleItems() {
        return items.filter(function (item) {
            return !item.closest(".gallery-col").hidden;
        });
    }

    function applyFilter(value) {
        var shown = 0;
        items.forEach(function (item) {
            var col = item.closest(".gallery-col");
            var match = value === "all" || col.dataset.category === value;
            col.hidden = !match;
            shown += match ? 1 : 0;
        });
        filters.forEach(function (button) {
            var active = button.dataset.filter === value;
            button.classList.toggle("active", active);
            button.setAttribute("aria-pressed", active ? "true" : "false");
        });
        if (empty) {
            empty.classList.toggle("d-none", shown > 0);
        }
    }

    filters.forEach(function (button) {
        button.addEventListener("click", function () {
            applyFilter(button.dataset.filter);
        });
    });

    /* -------------------------------------------------------------- lightbox */

    var box = document.createElement("div");
    box.className = "gallery-lightbox";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "Gallery image viewer");
    box.hidden = true;
    box.innerHTML =
        '<button type="button" class="gallery-lightbox-close" aria-label="Close">&times;</button>' +
        '<button type="button" class="gallery-lightbox-nav gallery-lightbox-prev" aria-label="Previous image">' +
        '<i class="bi bi-chevron-left"></i></button>' +
        '<figure class="gallery-lightbox-figure">' +
        '<img alt="">' +
        '<figcaption><span data-lightbox-title></span><span class="gallery-lightbox-count" data-lightbox-count></span></figcaption>' +
        "</figure>" +
        '<button type="button" class="gallery-lightbox-nav gallery-lightbox-next" aria-label="Next image">' +
        '<i class="bi bi-chevron-right"></i></button>';
    document.body.appendChild(box);

    var picture = box.querySelector("img");
    var titleSlot = box.querySelector("[data-lightbox-title]");
    var countSlot = box.querySelector("[data-lightbox-count]");
    var lastFocused = null;

    function show(index) {
        var shown = visibleItems();
        if (!shown.length) {
            return;
        }
        // Wrap around at both ends.
        current = (index + shown.length) % shown.length;
        var item = shown[current];
        picture.src = item.getAttribute("href");
        picture.alt = item.dataset.title || "";
        titleSlot.textContent = item.dataset.title || "";
        countSlot.textContent = current + 1 + " / " + shown.length;
    }

    function open(item) {
        lastFocused = document.activeElement;
        box.hidden = false;
        document.body.classList.add("gallery-lightbox-open");
        show(visibleItems().indexOf(item));
        box.querySelector(".gallery-lightbox-close").focus();
    }

    function close() {
        box.hidden = true;
        picture.removeAttribute("src");
        document.body.classList.remove("gallery-lightbox-open");
        if (lastFocused) {
            lastFocused.focus();
        }
    }

    items.forEach(function (item) {
        item.addEventListener("click", function (e) {
            e.preventDefault();
            open(item);
        });
    });

    box.querySelector(".gallery-lightbox-close").addEventListener("click", close);
    box.querySelector(".gallery-lightbox-prev").addEventListener("click", function () {
        show(current - 1);
    });
    box.querySelector(".gallery-lightbox-next").addEventListener("click", function () {
        show(current + 1);
    });

    // Clicking the backdrop closes; clicking the photo or a button does not.
    box.addEventListener("click", function (e) {
        if (e.target === box || e.target.classList.contains("gallery-lightbox-figure")) {
            close();
        }
    });

    document.addEventListener("keydown", function (e) {
        if (box.hidden) {
            return;
        }
        if (e.key === "Escape") {
            close();
        } else if (e.key === "ArrowLeft") {
            show(current - 1);
        } else if (e.key === "ArrowRight") {
            show(current + 1);
        }
    });

    // Swipe between photos on touch screens.
    var touchStart = null;
    box.addEventListener(
        "touchstart",
        function (e) {
            touchStart = e.changedTouches[0].clientX;
        },
        { passive: true }
    );
    box.addEventListener(
        "touchend",
        function (e) {
            if (touchStart === null) {
                return;
            }
            var travelled = e.changedTouches[0].clientX - touchStart;
            if (Math.abs(travelled) > 50) {
                show(travelled < 0 ? current + 1 : current - 1);
            }
            touchStart = null;
        },
        { passive: true }
    );

    // Deep link support: gallery.html#kitchens opens on that filter. Links from
    // elsewhere on this same page only change the hash without reloading, so the
    // filter has to follow hashchange too.
    function applyHash() {
        var requested = window.location.hash.replace("#", "");
        var known = filters.some(function (b) {
            return b.dataset.filter === requested;
        });
        applyFilter(known ? requested : "all");
    }

    window.addEventListener("hashchange", applyHash);
    applyHash();
})();
