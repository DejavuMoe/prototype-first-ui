/*
 * Review parameters for prototypes and previews.
 *
 *   ?theme=light|dark|system   ?density=compact|default|comfortable
 *   ?platform=web|desktop|ios|android   ?state=<id of a [data-state-view]>
 *
 * Applies them as attributes on <html> and shows the matching state view, so
 * every state has a stable URL for screenshots and DOM capture. Attributes the
 * page declares itself (for example data-platform="ios") stay in effect until a
 * parameter overrides them. Prototype-only: production code must not import it.
 */
(function installReviewParameters(doc, win) {
  "use strict";

  var RULES = {
    theme: /^(light|dark|system)$/,
    density: /^(compact|default|comfortable)$/,
    platform: /^(web|desktop|ios|android)$/,
    state: /^[a-z0-9][a-z0-9-]{0,39}$/
  };
  var NEUTRAL = { theme: "system", density: "default", platform: "web" };
  var ATTRIBUTES = ["theme", "density", "platform"];
  var root = doc.documentElement;
  var declared = {};
  var current = {};

  ATTRIBUTES.forEach(function remember(key) {
    var value = root.getAttribute("data-" + key);
    if (value && RULES[key].test(value)) declared[key] = value;
  });

  function readUrl() {
    var params = new URLSearchParams(win.location.search);
    Object.keys(RULES).forEach(function readKey(key) {
      var value = params.get(key);
      if (value && RULES[key].test(value)) current[key] = value;
    });
  }

  function effective(key) {
    return current[key] || declared[key] || NEUTRAL[key];
  }

  function setAttribute(key) {
    var value = effective(key);
    if (value === NEUTRAL[key]) root.removeAttribute("data-" + key);
    else root.setAttribute("data-" + key, value);
  }

  function stateViews() {
    return Array.prototype.slice.call(doc.querySelectorAll("[data-state-view]"));
  }

  function showState() {
    var views = stateViews();
    if (!views.length) return;
    var wanted = current.state || views[0].getAttribute("data-state-view");
    var found = views.some(function matches(view) { return view.getAttribute("data-state-view") === wanted; });
    views.forEach(function toggle(view, index) {
      view.hidden = found ? view.getAttribute("data-state-view") !== wanted : index !== 0;
    });
  }

  function writeUrl() {
    var url = new URL(win.location.href);
    Object.keys(RULES).forEach(function writeKey(key) {
      var value = current[key];
      var fallback = key === "state" ? undefined : (declared[key] || NEUTRAL[key]);
      if (value && value !== fallback) url.searchParams.set(key, value);
      else url.searchParams.delete(key);
    });
    win.history.replaceState(null, "", url.toString());
  }

  function apply(next, options) {
    Object.keys(next || {}).forEach(function merge(key) {
      if (!RULES[key]) return;
      if (next[key] === null || next[key] === undefined) delete current[key];
      else if (RULES[key].test(next[key])) current[key] = next[key];
    });
    ATTRIBUTES.forEach(setAttribute);
    showState();
    if (options && options.updateUrl) writeUrl();
    var detail = {};
    ATTRIBUTES.forEach(function report(key) { detail[key] = effective(key); });
    detail.state = current.state || null;
    doc.dispatchEvent(new CustomEvent("pfui:params", { detail: detail }));
  }

  readUrl();
  ATTRIBUTES.forEach(setAttribute);
  win.pfuiParams = {
    get: function get() {
      var values = {};
      ATTRIBUTES.forEach(function read(key) { values[key] = effective(key); });
      values.state = current.state || null;
      return values;
    },
    apply: apply,
    states: function states() {
      return stateViews().map(function name(view) { return view.getAttribute("data-state-view"); });
    }
  };
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", function ready() { apply(); });
  else apply();
})(document, window);
