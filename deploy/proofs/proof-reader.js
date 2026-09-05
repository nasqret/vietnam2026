/* Progressive enhancement only: no network, proof execution, or new authority. */
(function () {
  "use strict";
  function revealLine(hash) {
    var id;
    try { id = decodeURIComponent((hash || "").replace(/^#/, "")); }
    catch (_) { return; }
    if (!id) return;
    var target = document.getElementById(id);
    if (!target) return;
    var parent = target.parentElement;
    while (parent) {
      if (parent.tagName === "DETAILS") parent.open = true;
      parent = parent.parentElement;
    }
  }
  function ready() {
    document.querySelectorAll("[data-proof-reader]").forEach(function (reader) {
      if (reader.dataset.readerReady) return;
      reader.dataset.readerReady = "true";
      var toolbar = reader.querySelector("[data-reader-toolbar]");
      var groups = Array.from(reader.querySelectorAll("[data-reader-checkpoint]"));
      var ledger = reader.nextElementSibling;
      if (!toolbar || !ledger || !ledger.matches("[data-reader-exact]")) return;
      toolbar.hidden = false;
      var search = reader.querySelector("[data-reader-search]");
      var status = reader.querySelector("[data-reader-status]");
      var texts = groups.map(function (group) { return group.textContent.toLocaleLowerCase(); });
      var beforePrint = null;
      toolbar.addEventListener("click", function (event) {
        var button = event.target.closest("button[data-reader-action]");
        if (!button || !toolbar.contains(button)) return;
        var action = button.dataset.readerAction;
        if (action === "open" || action === "close") {
          groups.forEach(function (group) { if (!group.hidden) group.open = action === "open"; });
        } else if (action === "exact") {
          ledger.open = true;
          ledger.querySelector("summary").focus();
          ledger.scrollIntoView({block: "start"});
        }
      });
      search.addEventListener("input", function () {
        var term = search.value.trim().toLocaleLowerCase();
        var matches = 0;
        groups.forEach(function (group, index) {
          var found = !term || texts[index].indexOf(term) !== -1;
          group.hidden = !found;
          if (found) matches += 1;
        });
        status.textContent = term ? matches + " of " + groups.length + " checkpoints" : "";
      });
      reader.addEventListener("click", function (event) {
        var link = event.target.closest("a[data-reader-exact-line]");
        if (link && reader.contains(link)) revealLine(link.hash);
      });
      window.addEventListener("beforeprint", function () {
        if (beforePrint) return;
        beforePrint = groups.map(function (group) { return group.open; });
        groups.forEach(function (group) { if (!group.hidden) group.open = true; });
      });
      window.addEventListener("afterprint", function () {
        if (!beforePrint) return;
        groups.forEach(function (group, index) { group.open = beforePrint[index]; });
        beforePrint = null;
      });
    });
    revealLine(window.location.hash);
  }
  window.addEventListener("hashchange", function () { revealLine(window.location.hash); });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready, {once: true});
  else ready();
})();
