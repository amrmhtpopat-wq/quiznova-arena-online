/* TAG Teacher Mobile V4 — accessible dropdown; no auth/teacher-data writes. */
(function () {
  "use strict";
  function setup() {
    const sidebar = document.querySelector("#workspace > aside.sidebar");
    const toggle = document.getElementById("tagTeacherMobileToggle");
    const menu = document.getElementById("tagTeacherSections");
    if (!sidebar || !toggle || !menu) return;
    const phone = window.matchMedia("(max-width:650px)");
    function setOpen(open) {
      const expanded = !!open && phone.matches;
      sidebar.classList.toggle("tag-teacher-menu-open", expanded);
      toggle.setAttribute("aria-expanded", String(expanded));
      toggle.setAttribute("aria-label", expanded ? "إغلاق قائمة أقسام المعلم" : "فتح قائمة أقسام المعلم");
    }
    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    menu.addEventListener("click", function (event) {
      if (event.target.closest("button.nav[data-panel],a.nav[href]")) setOpen(false);
    });
    const studio = sidebar.querySelector("a.secondary.wide");
    if (studio) studio.addEventListener("click", function () { setOpen(false); });
    const logout = document.getElementById("logout");
    if (logout) logout.addEventListener("click", function () { setOpen(false); });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && sidebar.classList.contains("tag-teacher-menu-open")) {
        setOpen(false);
        toggle.focus();
      }
    });
    if (typeof phone.addEventListener === "function") {
      phone.addEventListener("change", function () { setOpen(false); });
    } else if (typeof phone.addListener === "function") {
      phone.addListener(function () { setOpen(false); });
    }
    setOpen(false);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup, { once: true });
  } else setup();
})();
