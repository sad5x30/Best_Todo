const siteLoader = document.querySelector("[data-site-loader]");

function hideSiteLoader() {
    if (!siteLoader) {
        return;
    }

    siteLoader.classList.add("is-hidden");
    document.body.classList.remove("is-loading");

    window.setTimeout(() => {
        siteLoader.remove();
    }, 500);
}

if (document.readyState === "complete") {
    window.setTimeout(hideSiteLoader, 450);
} else {
    window.addEventListener("load", () => {
        window.setTimeout(hideSiteLoader, 450);
    }, { once: true });
}

window.setTimeout(hideSiteLoader, 3200);
