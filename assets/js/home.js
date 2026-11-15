(() => {
  "use strict";

  function initialize() {
    // Keep existing links to the former one-page homepage working.
    const legacySections = {
      "#publications": ["publications", ""],
      "#-publications": ["publications", ""],
      "#experience": ["experience", ""],
      "#-educations": ["experience", "#-educations"],
      "#-invited-talks": ["experience", "#-invited-talks"],
      "#-services": ["experience", "#-services"],
      "#-teaching": ["experience", "#-teaching"],
      "#contact": ["contact", ""],
    };
    if (document.body.dataset.page === "home" && legacySections[window.location.hash]) {
      const [page, anchor] = legacySections[window.location.hash];
      const link = document.querySelector(`[data-nav="${page}"]`);
      if (link) {
        window.location.replace(link.href + anchor);
        return;
      }
    }

    const header = document.querySelector("[data-header]");
    const menuToggle = document.querySelector("[data-menu-toggle]");
    const navigation = document.getElementById("site-navigation");

    function closeMenu(returnFocus = false) {
      const wasOpen = document.body.classList.contains("menu-open");
      document.body.classList.remove("menu-open");
      menuToggle?.setAttribute("aria-expanded", "false");
      menuToggle?.setAttribute("aria-label", "Open navigation");
      if (returnFocus && wasOpen) menuToggle?.focus();
    }

    menuToggle?.addEventListener("click", () => {
      const isOpen = document.body.classList.toggle("menu-open");
      menuToggle.setAttribute("aria-expanded", String(isOpen));
      menuToggle.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
    });

    navigation?.addEventListener("click", (event) => {
      if (event.target.closest("a")) closeMenu();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeMenu(true);
    });

    const desktop = window.matchMedia("(min-width: 621px)");
    desktop.addEventListener("change", (event) => {
      if (event.matches) closeMenu();
    });

    if (header) {
      const updateHeader = () => {
        header.classList.toggle("is-scrolled", window.scrollY > 16);
      };
      updateHeader();
      window.addEventListener("scroll", updateHeader, { passive: true });
    }

    const publications = [...document.querySelectorAll("[data-publication]")];
    const publicationGroups = [...document.querySelectorAll("[data-publication-group]")];
    const search = document.getElementById("publication-search");
    const reset = document.getElementById("publication-reset");
    const empty = document.getElementById("publication-empty");
    const resultCount = document.getElementById("publication-count");

    const normalize = (value) => value
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase()
      .replace(/\s+/g, " ")
      .trim();

    const publicationText = new Map(publications.map((publication) => [
      publication,
      normalize(publication.textContent || ""),
    ]));

    function updatePublications() {
      const query = normalize(search?.value || "");
      const words = query.split(" ").filter(Boolean);
      let visibleCount = 0;

      publications.forEach((publication) => {
        publication.hidden = !words.every((word) => publicationText.get(publication).includes(word));
        if (!publication.hidden) visibleCount += 1;
      });

      publicationGroups.forEach((group) => {
        group.hidden = ![...group.querySelectorAll("[data-publication]")]
          .some((publication) => !publication.hidden);
      });

      if (resultCount) resultCount.textContent = `${visibleCount} ${visibleCount === 1 ? "work" : "works"}`;
      if (empty) empty.hidden = visibleCount !== 0;
      if (reset) reset.hidden = !query;
    }

    search?.addEventListener("input", updatePublications);
    reset?.addEventListener("click", () => {
      if (search) search.value = "";
      updatePublications();
      search?.focus();
    });

    if (publications.length) updatePublications();

    const currentPage = document.body.dataset.page;
    document.querySelectorAll(".nav-link[data-nav]").forEach((link) => {
      const isActive = Boolean(currentPage) && link.dataset.nav === currentPage;
      link.classList.toggle("is-active", isActive);
      if (isActive) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });

    const copyStatus = document.querySelector("[data-copy-status]");
    document.querySelectorAll("[data-copy-email]").forEach((button) => {
      const email = button.dataset.copyEmail;
      if (!email) return;
      const originalLabel = button.getAttribute("aria-label");
      let resetTimer;

      button.addEventListener("click", async () => {
        try {
          if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(email);
          } else {
            const input = document.createElement("textarea");
            input.value = email;
            input.setAttribute("readonly", "");
            input.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0";
            document.body.appendChild(input);
            input.select();
            const copied = document.execCommand("copy");
            input.remove();
            button.focus({ preventScroll: true });
            if (!copied) throw new Error("Copy unavailable");
          }

          window.clearTimeout(resetTimer);
          button.classList.add("is-copied");
          button.setAttribute("aria-label", "Email address copied");
          if (copyStatus) copyStatus.textContent = "Email address copied.";
          resetTimer = window.setTimeout(() => {
            button.classList.remove("is-copied");
            if (originalLabel) button.setAttribute("aria-label", originalLabel);
            else button.removeAttribute("aria-label");
            if (copyStatus) copyStatus.textContent = "";
          }, 2500);
        } catch {
          if (copyStatus) copyStatus.textContent = `Please copy the email address: ${email}`;
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
