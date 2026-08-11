/**
 * Enquiry form handler for the FormSubmit.co powered forms.
 *
 * Any form marked with data-enquiry-form is submitted in the background so the
 * visitor stays on the page. Without JavaScript the form still posts normally
 * and FormSubmit redirects to the page named in the _next field, so nothing is
 * lost when the script fails to load.
 *
 * Two things matter for the background submit to work:
 *   1. FormSubmit only sends CORS headers from its /ajax/ endpoint, so the
 *      plain action URL is rewritten before the fetch.
 *   2. FormSubmit rejects AJAX submissions when its captcha is on, so _captcha
 *      is set to false and the hidden _honey field catches bots instead.
 */
(function () {
    "use strict";

    var AJAX_ENDPOINT = /^(https?:\/\/(?:www\.)?formsubmit\.co\/)(?!ajax\/)/i;

    function ajaxUrl(action) {
        return action.replace(AJAX_ENDPOINT, "$1ajax/");
    }

    function show(el, message) {
        if (!el) {
            return;
        }
        if (message) {
            var slot = el.querySelector("[data-message]");
            if (slot) {
                slot.textContent = message;
            }
        }
        el.classList.remove("d-none");
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function hide(el) {
        if (el) {
            el.classList.add("d-none");
        }
    }

    function setBusy(form, busy) {
        var button = form.querySelector("[type=submit]");
        if (!button) {
            return;
        }
        button.disabled = busy;
        var idle = button.querySelector("[data-btn-text]");
        var sending = button.querySelector("[data-btn-spinner]");
        if (idle) {
            idle.classList.toggle("d-none", busy);
        }
        if (sending) {
            sending.classList.toggle("d-none", !busy);
        }
    }

    function handle(form) {
        var success = form.querySelector("[data-form-success]");
        var error = form.querySelector("[data-form-error]");

        form.addEventListener("submit", function (e) {
            // Let the browser show its own messages on an incomplete form.
            if (!form.checkValidity()) {
                form.classList.add("was-validated");
                return;
            }

            e.preventDefault();
            hide(success);
            hide(error);
            setBusy(form, true);

            fetch(ajaxUrl(form.action), {
                method: "POST",
                body: new FormData(form),
                headers: { Accept: "application/json" }
            })
                .then(function (response) {
                    return response
                        .json()
                        .catch(function () {
                            return {};
                        })
                        .then(function (data) {
                            if (!response.ok || String(data.success) === "false") {
                                throw new Error(data.message || "Form submission failed");
                            }
                            return data;
                        });
                })
                .then(function (data) {
                    setBusy(form, false);
                    form.reset();
                    form.classList.remove("was-validated");
                    // FormSubmit asks the owner to confirm a new address on the
                    // very first send. Passing its message through makes that
                    // visible instead of a plain "sent" that never arrives.
                    show(success, data.message);
                })
                .catch(function (err) {
                    setBusy(form, false);
                    show(error);
                    console.error("Enquiry form error:", err);
                });
        });
    }

    document.querySelectorAll("form[data-enquiry-form]").forEach(handle);
})();
