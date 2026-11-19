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
		/* Short last section: its top may never cross the activation line
		   before the page bottoms out — highlight it at (near) max scroll. */
		var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
		if (window.innerHeight > 0 && window.scrollY >= maxScroll - 2) {
			current = sections[sections.length - 1];
		}
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
	/* ---- Theme toggle: auto → light → dark → auto -------------------- */
	/* Auto (attribute removed) follows the OS via the CSS media query.
	   The inline <head> bootstrap already applied any stored choice, so
	   there is no flash; here we only cycle and persist the next state. */
	var themeBtn = document.getElementById("theme-toggle");

	function themeState() {
		var a = document.documentElement.getAttribute("data-theme");
		return a === "light" || a === "dark" ? a : "auto";
	}

	function applyTheme(next) {
		var root = document.documentElement;
		if (next === "auto") {
			root.removeAttribute("data-theme");
			try { localStorage.removeItem("theme"); } catch (e) {}
		} else {
			root.setAttribute("data-theme", next);
			try { localStorage.setItem("theme", next); } catch (e) {}
		}
		paintThemeBtn();
	}

	/* Icon + label reflect the *current* state; tooltip names the next. */
	function paintThemeBtn() {
		if (!themeBtn) return;
		var s = themeState();
		var glyphs = { auto: "\u2699", light: "\u263C", dark: "\u263E" };
		var nexts = { auto: "light", light: "dark", dark: "auto" };
		themeBtn.innerHTML = glyphs[s];
		themeBtn.title = "Theme: " + s + " (click for " + nexts[s] + ")";
		themeBtn.setAttribute(
			"aria-label",
			"Color theme: " + s + ". Activate to switch to " + nexts[s] + "."
		);
	}

	if (themeBtn) {
		paintThemeBtn();
		themeBtn.addEventListener("click", function () {
			applyTheme({ auto: "light", light: "dark", dark: "auto" }[themeState()]);
		});
	}
})();
