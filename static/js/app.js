/* ── Search Engine UI Logic ─────────────────────────── */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    setupClearButtons();
    setupFormSubmit();
    focusSearchInput();
  }

  /** Show/hide the X button inside search inputs */
  function setupClearButtons() {
    document.querySelectorAll(".search-input-wrap").forEach(function (wrap) {
      var input = wrap.querySelector('input[type="text"]');
      var btn = wrap.querySelector(".clear-btn");
      if (!input || !btn) return;

      function toggle() {
        btn.classList.toggle("visible", input.value.length > 0);
      }

      input.addEventListener("input", toggle);
      btn.addEventListener("click", function () {
        input.value = "";
        toggle();
        input.focus();
      });

      toggle();
    });
  }

  /** Auto-focus the main search input on the home page */
  function focusSearchInput() {
    var home = document.querySelector(".home-wrapper");
    if (home) {
      var input = home.querySelector('input[name="q"]');
      if (input) input.focus();
    }
  }

  /** Handle form submission — build clean URL */
  function setupFormSubmit() {
    document.querySelectorAll("form.search-form").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();

        var params = new URLSearchParams();
        var q = form.querySelector('[name="q"]');
        var source = form.querySelector('[name="source"]');
        var sinceHours = form.querySelector('[name="since_hours"]');

        if (q && q.value.trim()) {
          params.set("q", q.value.trim());
        }
        if (source && source.value) {
          params.set("source", source.value);
        }
        if (sinceHours && sinceHours.value && sinceHours.value !== "24") {
          params.set("since_hours", sinceHours.value);
        }

        var qs = params.toString();
        window.location.href = "/search" + (qs ? "?" + qs : "");
      });
    });

    /* Also handle the filter bar apply button */
    var filterForm = document.getElementById("filter-form");
    if (filterForm) {
      filterForm.addEventListener("submit", function (e) {
        e.preventDefault();

        var params = new URLSearchParams(window.location.search);
        var source = filterForm.querySelector('[name="source"]');
        var sinceHours = filterForm.querySelector('[name="since_hours"]');

        if (source) {
          if (source.value) {
            params.set("source", source.value);
          } else {
            params.delete("source");
          }
        }
        if (sinceHours) {
          if (sinceHours.value && sinceHours.value !== "24") {
            params.set("since_hours", sinceHours.value);
          } else {
            params.delete("since_hours");
          }
        }

        var qs = params.toString();
        window.location.href = "/search" + (qs ? "?" + qs : "");
      });
    }
  }
})();
