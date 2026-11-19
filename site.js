/* Progressive enhancement only: the site is fully readable without JS.
   Adds: .js class, sticky-header shadow, nav scroll-spy, section reveals,
   publication category filter, back-to-top button. */
(function () {
	"use strict";

	document.documentElement.classList.add("js");

	/* ---- Sticky header shadow -------------------------------------- */
	var header = document.querySelector(".site-header");

	function onScroll() {
		if (header) header.classList.toggle("scrolled", window.scrollY > 8);
	}
	window.addEventListener("scroll", onScroll, { passive: true });
	onScroll();

	/* ---- Nav scroll-spy (IntersectionObserver, cheap) --------------- */
	var navLinks = Array.prototype.slice.call(
		document.querySelectorAll(".site-nav a[href^='#']")
	);
	var sections = navLinks
		.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); })
		.filter(Boolean);

	function spy() {
		var pos = window.scrollY + 120;
		var current = sections[0];
		sections.forEach(function (s) { if (s.offsetTop <= pos) current = s; });
		navLinks.forEach(function (a) {
			a.classList.toggle("current", current && a.getAttribute("href") === "#" + current.id);
		});
	}
	window.addEventListener("scroll", spy, { passive: true });
	spy();

	/* ---- Publication category filter -------------------------------- */
	var filterBox = document.querySelector(".pub-filters");
	if (filterBox) {
		var buttons = filterBox.querySelectorAll("button[data-cat]");
		var lists = document.querySelectorAll("#publications > h3 + ul");

		buttons.forEach(function (btn) {
			btn.addEventListener("click", function () {
				var cat = btn.getAttribute("data-cat");
				buttons.forEach(function (b) {
					var active = b === btn;
					b.classList.toggle("active", active);
					b.setAttribute("aria-pressed", active ? "true" : "false");
				});
				lists.forEach(function (ul) {
					var h3 = ul.previousElementSibling; // the <h3> category heading
					var match = cat === "all" || (h3 && h3.textContent.trim() === cat);
					ul.classList.toggle("cat-hidden", !match);
					if (h3) h3.classList.toggle("cat-hidden", !match);
				});
			});
		});
	}

	/* ---- Section reveal on scroll ------------------------------------ */
	var reveals = document.querySelectorAll(".reveal");
	if ("IntersectionObserver" in window) {
		var io = new IntersectionObserver(function (entries) {
			entries.forEach(function (e) {
				if (e.isIntersecting) {
					e.target.classList.add("in");
					io.unobserve(e.target);
				}
			});
		}, { threshold: 0.06 });
		reveals.forEach(function (el) { io.observe(el); });
	} else {
		reveals.forEach(function (el) { el.classList.add("in"); });
	}

	/* ---- Back to top -------------------------------------------------- */
	var totop = document.getElementById("totop");
	if (totop) {
		totop.addEventListener("click", function () {
			window.scrollTo({ top: 0, behavior: "smooth" });
		});
		window.addEventListener("scroll", function () {
			totop.classList.toggle("visible", window.scrollY > 600);
		}, { passive: true });
	}
})();
