/*
 * Deck navigation: arrow keys / PageUp / PageDown / Space / Home / End,
 * click right or left half, ?slide=N for a stable URL per slide, "n" or
 * ?notes=1 for speaker notes. Prototype tooling only.
 */
(function deck(doc, win) {
  "use strict";

  var slides = Array.prototype.slice.call(doc.querySelectorAll(".slide"));
  var notes = doc.querySelector(".deck__notes");
  var params = new URLSearchParams(win.location.search);
  var index = clamp(parseInt(params.get("slide") || "1", 10) - 1);

  if (params.get("notes") === "1") doc.documentElement.setAttribute("data-notes", "");
  slides.forEach(function number(slide, position) { slide.setAttribute("data-number", String(position + 1)); });

  function clamp(value) {
    if (isNaN(value)) return 0;
    return Math.max(0, Math.min(slides.length - 1, value));
  }

  function fit() {
    var scale = Math.min(win.innerWidth / 1920, win.innerHeight / 1080);
    doc.documentElement.style.setProperty("--deck-scale", String(scale));
  }

  function show(next) {
    index = clamp(next);
    slides.forEach(function toggle(slide, position) {
      slide.classList.toggle("is-current", position === index);
    });
    var url = new URL(win.location.href);
    if (index === 0) url.searchParams.delete("slide");
    else url.searchParams.set("slide", String(index + 1));
    win.history.replaceState(null, "", url.toString());
    if (notes) {
      var source = slides[index] && slides[index].querySelector(".notes");
      notes.textContent = source ? source.textContent.trim() : "";
    }
  }

  doc.addEventListener("keydown", function onKey(event) {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    var key = event.key;
    if (key === "ArrowRight" || key === "PageDown" || key === " ") show(index + 1);
    else if (key === "ArrowLeft" || key === "PageUp") show(index - 1);
    else if (key === "Home") show(0);
    else if (key === "End") show(slides.length - 1);
    else if (key === "n") doc.documentElement.toggleAttribute("data-notes");
    else return;
    event.preventDefault();
  });

  doc.addEventListener("click", function onClick(event) {
    if (event.target.closest("a, button, input, select, textarea, .deck__notes")) return;
    show(event.clientX > win.innerWidth / 2 ? index + 1 : index - 1);
  });

  win.addEventListener("resize", fit);
  fit();
  show(index);
})(document, window);
