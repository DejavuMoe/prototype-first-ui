/*
 * Prototype behavior.
 *
 * - Every state is reachable by URL (?state=ready|loading|empty|error) through
 *   styles/params.js, so reviews and screenshots never depend on clicking.
 * - data-go="loading -> ready" simulates an async flow, showing each state in
 *   order. Simulated effects are prototype-only: say so in the handoff, never in
 *   the interface.
 * - Build the ready view from window.FIXTURES (fixtures.js). Fixtures stay
 *   synthetic: no real customer data, credentials, private URLs or local paths.
 */
(function prototype(doc, win) {
  "use strict";

  var STEP_DELAY = 700;
  var timer = null;

  function go(steps) {
    if (timer) win.clearTimeout(timer);
    var queue = steps.slice();
    (function next() {
      var state = queue.shift();
      if (!state) return;
      win.pfuiParams.apply({ state: state }, { updateUrl: true });
      if (queue.length) timer = win.setTimeout(next, STEP_DELAY);
    })();
  }

  function renderReady(container, fixtures) {
    if (!container || !fixtures) return;
    // Replace the ready.content slot in index.html with markup built here
    // from fixtures, or write the ready view directly in HTML. Either way the
    // copy must trace to evidence or approved content.
  }

  doc.addEventListener("click", function onClick(event) {
    var trigger = event.target.closest("[data-go]");
    if (!trigger) return;
    event.preventDefault();
    go(trigger.getAttribute("data-go").split(/\s*->\s*/).filter(Boolean));
  });

  doc.addEventListener("pfui:params", function onParams(event) {
    var main = doc.getElementById("main");
    if (main) main.setAttribute("aria-busy", String(event.detail.state === "loading"));
  });

  doc.addEventListener("DOMContentLoaded", function ready() {
    renderReady(doc.getElementById("ready-content"), win.FIXTURES || null);
  });
})(document, window);
