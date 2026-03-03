/* ── SearchEngine — Client-side search over articles.json ── */
(function () {
  "use strict";

  var allArticles = [];
  var dataLoaded = false;

  // ── DOM refs ──────────────────────────────────────────
  var homeView     = document.getElementById("home-view");
  var resultsView  = document.getElementById("results-view");
  var homeForm     = document.getElementById("home-form");
  var resultsForm  = document.getElementById("results-form");
  var homeQ        = document.getElementById("home-q");
  var resultsQ     = document.getElementById("results-q");
  var homeSource   = document.getElementById("home-source");
  var homeHours    = document.getElementById("home-hours");
  var filterSource = document.getElementById("filter-source");
  var filterHours  = document.getElementById("filter-hours");
  var filterApply  = document.getElementById("filter-apply");
  var resultsList  = document.getElementById("results-list");
  var resultsStats = document.getElementById("results-stats");
  var loading      = document.getElementById("loading");
  var backHome     = document.getElementById("back-home");

  // ── Init ──────────────────────────────────────────────
  function init() {
    setupClearButtons();
    bindEvents();
    loadData();
    readURL();
  }

  // ── Load articles.json ────────────────────────────────
  function loadData() {
    loading.classList.add("active");
    fetch("data/articles.json")
      .then(function (r) {
        if (!r.ok) throw new Error("No data yet");
        return r.json();
      })
      .then(function (data) {
        allArticles = data;
        dataLoaded = true;
        populateSourceDropdowns();
        loading.classList.remove("active");
        // If URL had search params, execute the search now
        readURL();
      })
      .catch(function () {
        allArticles = [];
        dataLoaded = true;
        loading.classList.remove("active");
        readURL();
      });
  }

  // ── Populate source dropdowns ─────────────────────────
  function populateSourceDropdowns() {
    var sources = {};
    allArticles.forEach(function (a) {
      if (a.source) sources[a.source] = true;
    });
    var names = Object.keys(sources).sort();

    [homeSource, filterSource].forEach(function (sel) {
      sel.innerHTML = '<option value="">All sources</option>';
      names.forEach(function (name) {
        var opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name;
        sel.appendChild(opt);
      });
    });
  }

  // ── Bind events ───────────────────────────────────────
  function bindEvents() {
    homeForm.addEventListener("submit", function (e) {
      e.preventDefault();
      doSearch(homeQ.value, homeSource.value, homeHours.value);
    });

    document.getElementById("home-search-btn").addEventListener("click", function () {
      doSearch(homeQ.value, homeSource.value, homeHours.value);
    });

    resultsForm.addEventListener("submit", function (e) {
      e.preventDefault();
      doSearch(resultsQ.value, filterSource.value, filterHours.value);
    });

    filterApply.addEventListener("click", function () {
      doSearch(resultsQ.value, filterSource.value, filterHours.value);
    });

    backHome.addEventListener("click", function (e) {
      e.preventDefault();
      showHome();
    });

    // Enter key on results search box
    resultsQ.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        doSearch(resultsQ.value, filterSource.value, filterHours.value);
      }
    });
  }

  // ── URL state management ──────────────────────────────
  function readURL() {
    if (!dataLoaded) return;
    var params = new URLSearchParams(window.location.search);
    var q = params.get("q") || "";
    var source = params.get("source") || "";
    var hours = params.get("since_hours") || "168";

    if (q || source || params.has("since_hours")) {
      homeQ.value = q;
      homeSource.value = source;
      homeHours.value = hours;
      executeSearch(q, source, parseInt(hours, 10));
    }
  }

  function pushURL(q, source, hours) {
    var params = new URLSearchParams();
    if (q) params.set("q", q);
    if (source) params.set("source", source);
    if (hours && String(hours) !== "168") params.set("since_hours", hours);
    var qs = params.toString();
    var url = window.location.pathname + (qs ? "?" + qs : "");
    history.pushState(null, "", url);
  }

  // ── Search logic ──────────────────────────────────────
  function doSearch(q, source, hours) {
    q = (q || "").trim();
    hours = parseInt(hours, 10) || 168;
    pushURL(q, source, hours);
    executeSearch(q, source, hours);
  }

  function executeSearch(q, source, hours) {
    // Switch to results view
    homeView.style.display = "none";
    resultsView.style.display = "flex";

    // Sync controls
    resultsQ.value = q;
    filterSource.value = source;
    filterHours.value = hours;

    var now = new Date();
    var cutoff = new Date(now.getTime() - hours * 3600000);
    var keywords = q.toLowerCase().split(/\s+/).filter(Boolean);

    var filtered = allArticles.filter(function (art) {
      // Time filter
      var ts = art.published_at || art.created_at || "";
      if (ts && new Date(ts) < cutoff) return false;

      // Source filter
      if (source && art.source !== source) return false;

      // Keyword filter
      if (keywords.length > 0) {
        var haystack = ((art.title || "") + " " + (art.snippet || "")).toLowerCase();
        for (var i = 0; i < keywords.length; i++) {
          if (haystack.indexOf(keywords[i]) === -1) return false;
        }
      }

      return true;
    });

    renderResults(filtered, q, hours);
  }

  // ── Render results ────────────────────────────────────
  function renderResults(articles, q, hours) {
    var countText = articles.length + " result" + (articles.length !== 1 ? "s" : "");
    if (q) countText += ' for <strong>' + escapeHTML(q) + '</strong>';
    countText += " (past " + hours + "h)";
    resultsStats.innerHTML = countText;

    if (articles.length === 0) {
      resultsList.innerHTML =
        '<div class="no-results">' +
        '<h2>No results found' + (q ? ' for "' + escapeHTML(q) + '"' : '') + '</h2>' +
        '<p>Try different keywords, a broader time range, or check that news has been ingested.</p>' +
        '</div>';
      return;
    }

    var html = "";
    articles.forEach(function (art) {
      var snippet = (art.snippet || "").substring(0, 300);
      if ((art.snippet || "").length > 300) snippet += "\u2026";

      // Highlight keywords in title and snippet
      var titleHTML = escapeHTML(art.title);
      var snippetHTML = escapeHTML(snippet);
      if (q) {
        var words = q.trim().split(/\s+/);
        words.forEach(function (w) {
          if (!w) return;
          var re = new RegExp("(" + escapeRegex(w) + ")", "gi");
          titleHTML = titleHTML.replace(re, "<mark>$1</mark>");
          snippetHTML = snippetHTML.replace(re, "<mark>$1</mark>");
        });
      }

      var displayURL = (art.url || "").replace(/^https?:\/\//, "");
      if (displayURL.length > 80) displayURL = displayURL.substring(0, 77) + "\u2026";

      var dateStr = "";
      try {
        var d = new Date(art.published_at || art.created_at);
        dateStr = d.toLocaleDateString("en-US", {
          year: "numeric", month: "short", day: "numeric",
          hour: "2-digit", minute: "2-digit",
        });
      } catch (e) { /* ignore */ }

      html +=
        '<div class="result-card">' +
          '<div class="result-url">' +
            '<span class="favicon">' + escapeHTML((art.source || "?")[0]).toUpperCase() + '</span>' +
            escapeHTML(displayURL) +
          '</div>' +
          '<h3 class="result-title">' +
            '<a href="' + escapeAttr(art.url) + '" target="_blank" rel="noopener noreferrer">' +
              titleHTML +
            '</a>' +
          '</h3>' +
          '<div class="result-snippet">' + snippetHTML + '</div>' +
          '<div class="result-meta">' +
            '<span class="source-badge ' + escapeAttr(art.source_type || "") + '">' +
              escapeHTML(art.source_type || "") +
            '</span>' +
            '<span>' + escapeHTML(art.source || "") + '</span>' +
            '<span>&middot;</span>' +
            '<span>' + escapeHTML(dateStr) + '</span>' +
          '</div>' +
        '</div>';
    });

    resultsList.innerHTML = html;
  }

  // ── Show home view ────────────────────────────────────
  function showHome() {
    resultsView.style.display = "none";
    homeView.style.display = "flex";
    history.pushState(null, "", window.location.pathname);
    homeQ.focus();
  }

  // ── Clear buttons ─────────────────────────────────────
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

  // ── Utilities ─────────────────────────────────────────
  function escapeHTML(s) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(s || ""));
    return div.innerHTML;
  }

  function escapeAttr(s) {
    return (s || "").replace(/&/g, "&amp;").replace(/"/g, "&quot;")
                     .replace(/'/g, "&#39;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  // ── Handle browser back/forward ───────────────────────
  window.addEventListener("popstate", function () {
    var params = new URLSearchParams(window.location.search);
    if (!params.has("q") && !params.has("source") && !params.has("since_hours")) {
      showHome();
    } else {
      readURL();
    }
  });

  // ── Boot ──────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", init);
})();
