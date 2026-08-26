/* Progressive enhancement for the arithmetic theorem atlas and study route. */
(function () {
  "use strict";

  function whenReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function theoremLink(name, label) {
    var link = document.createElement("a");
    link.className = "pa-focus-node";
    link.href = "#theorem-" + name;
    link.dataset.theoremLink = name;
    var code = document.createElement("code");
    code.textContent = label || name;
    link.appendChild(code);
    return link;
  }

  function initializeAtlas(atlas) {
    var cards = Array.from(atlas.querySelectorAll(".pa-theorem-card"));
    var checkedCards = cards.filter(function (card) {
      return card.dataset.status !== "blocked_by_language";
    });
    var byName = new Map(checkedCards.map(function (card) {
      return [card.dataset.name, card];
    }));
    var dependents = new Map(checkedCards.map(function (card) {
      return [card.dataset.name, []];
    }));
    checkedCards.forEach(function (card) {
      var dependencies = (card.dataset.dependencies || "").split(",").filter(Boolean);
      dependencies.forEach(function (dependency) {
        if (dependents.has(dependency)) {
          dependents.get(dependency).push(card.dataset.name);
        }
      });
    });

    var search = atlas.querySelector("[data-pa-search]");
    var domain = atlas.querySelector("[data-pa-domain]");
    var status = atlas.querySelector("[data-pa-status]");
    var clear = atlas.querySelector("[data-pa-clear]");
    var count = atlas.querySelector("[data-pa-count]");
    var focus = atlas.querySelector("[data-pa-focus]");
    var hops = atlas.querySelector("[data-pa-hops]");
    var focusGraph = atlas.querySelector("[data-pa-focus-graph]");

    function applyFilters() {
      var query = search.value.trim().toLowerCase();
      var domainValue = domain.value;
      var statusValue = status.value;
      var visible = 0;
      cards.forEach(function (card) {
        var statusMatch = statusValue === "all" ||
          (statusValue === "checked" && card.dataset.status !== "blocked_by_language") ||
          card.dataset.status === statusValue;
        var show = (!query || card.dataset.search.indexOf(query) !== -1) &&
          (domainValue === "all" || card.dataset.domain === domainValue) &&
          statusMatch;
        card.hidden = !show;
        if (show) visible += 1;
      });
      count.value = visible + (visible === 1 ? " entry" : " entries");
      count.textContent = count.value;
    }

    function column(title, entries, emptyText) {
      var section = document.createElement("section");
      section.className = "pa-focus-column";
      var heading = document.createElement("h3");
      heading.textContent = title;
      section.appendChild(heading);
      if (!entries.length) {
        var empty = document.createElement("span");
        empty.className = "pa-empty-relation";
        empty.textContent = emptyText;
        section.appendChild(empty);
      } else {
        entries.slice(0, 14).forEach(function (entry) {
          var link = theoremLink(entry.name);
          if (entry.distance > 1) {
            var distance = document.createElement("span");
            distance.className = "pa-hop-distance";
            distance.textContent = entry.distance + " hops away";
            link.appendChild(distance);
          }
          section.appendChild(link);
        });
        if (entries.length > 14) {
          var more = document.createElement("small");
          more.textContent = "+ " + (entries.length - 14) + " more in this neighborhood";
          section.appendChild(more);
        }
      }
      return section;
    }

    function arrow() {
      var node = document.createElement("span");
      node.className = "pa-focus-arrow";
      node.setAttribute("aria-hidden", "true");
      node.textContent = "→";
      return node;
    }

    function neighborhood(seed, direction, maximumDepth) {
      var queue = [{ name: seed, distance: 0 }];
      var seen = new Set([seed]);
      var result = [];
      while (queue.length) {
        var current = queue.shift();
        if (current.distance >= maximumDepth) continue;
        var next;
        if (direction === "backward") {
          var node = byName.get(current.name);
          next = node ? (node.dataset.dependencies || "").split(",").filter(Boolean) : [];
        } else {
          next = dependents.get(current.name) || [];
        }
        next.forEach(function (name) {
          if (seen.has(name)) return;
          seen.add(name);
          var entry = { name: name, distance: current.distance + 1 };
          result.push(entry);
          queue.push(entry);
        });
      }
      return result.sort(function (left, right) {
        return left.distance - right.distance || left.name.localeCompare(right.name);
      });
    }

    function renderFocus(name) {
      var card = byName.get(name);
      if (!card) return;
      focus.value = name;
      focusGraph.replaceChildren();
      var depth = Number(hops.value || 2);
      var dependencies = neighborhood(name, "backward", depth);
      focusGraph.appendChild(column("Earlier prerequisites", dependencies, "root theorem"));
      focusGraph.appendChild(arrow());
      var current = document.createElement("section");
      current.className = "pa-focus-current";
      var heading = document.createElement("h3");
      heading.textContent = "Selected";
      current.appendChild(heading);
      current.appendChild(theoremLink(name));
      var receipt = document.createElement("small");
      var nodes = card.querySelector(".pa-proof-receipt dd");
      receipt.textContent = card.dataset.domain.replace("_", " ") +
        (nodes ? " · " + nodes.textContent + " nodes" : "");
      current.appendChild(receipt);
      focusGraph.appendChild(current);
      focusGraph.appendChild(arrow());
      focusGraph.appendChild(column("Later clients", neighborhood(name, "forward", depth), "terminal theorem"));
    }

    function revealTheorem(name, shouldScroll) {
      var card = byName.get(name);
      if (!card) return;
      if (card.hidden) {
        search.value = "";
        domain.value = "all";
        status.value = "all";
        applyFilters();
      }
      atlas.querySelectorAll(".pa-selected").forEach(function (node) {
        node.classList.remove("pa-selected");
      });
      card.classList.add("pa-selected");
      var details = card.querySelector(":scope > details");
      if (details) details.open = true;
      renderFocus(name);
      if (shouldScroll) {
        var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        card.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
      }
    }

    search.addEventListener("input", applyFilters);
    domain.addEventListener("change", applyFilters);
    status.addEventListener("change", applyFilters);
    clear.addEventListener("click", function () {
      search.value = "";
      domain.value = "all";
      status.value = "all";
      applyFilters();
      search.focus();
    });
    focus.addEventListener("change", function () {
      window.location.hash = "theorem-" + focus.value;
    });
    hops.addEventListener("change", function () {
      renderFocus(focus.value);
    });

    atlas.addEventListener("click", function (event) {
      var link = event.target.closest("[data-theorem-link]");
      if (!link) return;
      var name = link.dataset.theoremLink;
      if (!byName.has(name)) return;
      event.preventDefault();
      var nextHash = "#theorem-" + name;
      if (window.location.hash === nextHash) {
        revealTheorem(name, true);
      } else {
        window.location.hash = nextHash;
      }
    });

    atlas.addEventListener("click", function (event) {
      var button = event.target.closest("[data-copy-target]");
      if (!button) return;
      var target = document.getElementById(button.dataset.copyTarget);
      if (!target) return;
      var text = target.textContent;
      var copied = function () {
        var original = button.textContent;
        button.textContent = "Copied";
        window.setTimeout(function () { button.textContent = original; }, 1300);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(copied);
      } else {
        var area = document.createElement("textarea");
        area.value = text;
        area.style.position = "fixed";
        area.style.opacity = "0";
        document.body.appendChild(area);
        area.select();
        document.execCommand("copy");
        area.remove();
        copied();
      }
    });

    window.addEventListener("hashchange", function () {
      var match = window.location.hash.match(/^#theorem-(.+)$/);
      if (match) revealTheorem(decodeURIComponent(match[1]), true);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "/" && !/INPUT|SELECT|TEXTAREA/.test(event.target.tagName)) {
        event.preventDefault();
        search.focus();
      }
    });

    applyFilters();
    var initial = window.location.hash.match(/^#theorem-(.+)$/);
    revealTheorem(initial ? decodeURIComponent(initial[1]) : "fundamental_theorem_of_arithmetic", false);
  }

  function initializeLearningRoute(route) {
    var storageKey = "pa-arithmetic-learning-route-v1";
    var boxes = Array.from(route.querySelectorAll("[data-learning-step]"));
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(storageKey) || "{}"); } catch (_error) { saved = {}; }
    boxes.forEach(function (box) {
      box.checked = Boolean(saved[box.dataset.learningStep]);
      box.addEventListener("change", function () {
        saved[box.dataset.learningStep] = box.checked;
        try { localStorage.setItem(storageKey, JSON.stringify(saved)); } catch (_error) { /* read-only browser */ }
      });
    });
    var reset = route.querySelector("[data-route-reset]");
    if (reset) {
      reset.addEventListener("click", function () {
        saved = {};
        boxes.forEach(function (box) { box.checked = false; });
        try { localStorage.removeItem(storageKey); } catch (_error) { /* read-only browser */ }
      });
    }
  }

  whenReady(function () {
    document.querySelectorAll("[data-pa-atlas]").forEach(initializeAtlas);
    document.querySelectorAll("[data-pa-learning-route]").forEach(initializeLearningRoute);
  });
}());
