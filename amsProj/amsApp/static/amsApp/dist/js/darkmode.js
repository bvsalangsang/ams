document.addEventListener("DOMContentLoaded", function () {
	const darkModeSwitch = document.getElementById("darkModeSwitch");
	const sidebarMiniSwitch = document.getElementById("sidebarMiniSwitch");

	const smallBodyText = document.getElementById("smallBodyText");
	const smallNavbarText = document.getElementById("smallNavbarText");
	const smallBrandText = document.getElementById("smallBrandText");
	const smallSidebarText = document.getElementById("smallSidebarText");
	const smallFooterText = document.getElementById("smallFooterText");

	const body = document.body;
	const navbar = document.querySelector(".main-header");
	const brand = document.querySelector(".brand-link");
	const sidebarNav = document.querySelector(".nav-sidebar");
	const footer = document.querySelector(".main-footer");

	// Load saved settings from localStorage
	if (localStorage.getItem("dark-mode") === "enabled") {
		body.classList.add("dark-mode");
		darkModeSwitch.checked = true;
	}
	if (localStorage.getItem("sidebar-mini") === "enabled") {
		body.classList.add("sidebar-mini");
		sidebarMiniSwitch.checked = true;
	}
	if (localStorage.getItem("small-body-text") === "enabled") {
		body.classList.add("text-sm");
		smallBodyText.checked = true;
	}
	if (localStorage.getItem("small-navbar-text") === "enabled") {
		navbar.classList.add("text-sm");
		smallNavbarText.checked = true;
	}
	if (localStorage.getItem("small-brand-text") === "enabled") {
		brand.classList.add("text-sm");
		smallBrandText.checked = true;
	}
	if (localStorage.getItem("small-sidebar-text") === "enabled") {
		sidebarNav.classList.add("text-sm");
		smallSidebarText.checked = true;
	}
	if (localStorage.getItem("small-footer-text") === "enabled") {
		footer.classList.add("text-sm");
		smallFooterText.checked = true;
	}

	// Dark Mode Toggle
	darkModeSwitch.addEventListener("change", function () {
		if (darkModeSwitch.checked) {
			body.classList.add("dark-mode");
			localStorage.setItem("dark-mode", "enabled");
		} else {
			body.classList.remove("dark-mode");
			localStorage.setItem("dark-mode", "disabled");
		}
	});

	// Sidebar Mini Toggle
	sidebarMiniSwitch.addEventListener("change", function () {
		if (sidebarMiniSwitch.checked) {
			body.classList.add("sidebar-mini");
			localStorage.setItem("sidebar-mini", "enabled");
		} else {
			body.classList.remove("sidebar-mini");
			localStorage.setItem("sidebar-mini", "disabled");
		}
	});

	// Small Text Toggles
	smallBodyText.addEventListener("change", function () {
		body.classList.toggle("text-sm", smallBodyText.checked);
		localStorage.setItem(
			"small-body-text",
			smallBodyText.checked ? "enabled" : "disabled"
		);
	});

	smallNavbarText.addEventListener("change", function () {
		navbar.classList.toggle("text-sm", smallNavbarText.checked);
		localStorage.setItem(
			"small-navbar-text",
			smallNavbarText.checked ? "enabled" : "disabled"
		);
	});

	smallBrandText.addEventListener("change", function () {
		brand.classList.toggle("text-sm", smallBrandText.checked);
		localStorage.setItem(
			"small-brand-text",
			smallBrandText.checked ? "enabled" : "disabled"
		);
	});

	smallSidebarText.addEventListener("change", function () {
		sidebarNav.classList.toggle("text-sm", smallSidebarText.checked);
		localStorage.setItem(
			"small-sidebar-text",
			smallSidebarText.checked ? "enabled" : "disabled"
		);
	});

	smallFooterText.addEventListener("change", function () {
		footer.classList.toggle("text-sm", smallFooterText.checked);
		localStorage.setItem(
			"small-footer-text",
			smallFooterText.checked ? "enabled" : "disabled"
		);
	});
});
