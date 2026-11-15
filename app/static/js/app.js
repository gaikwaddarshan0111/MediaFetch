
const PLATFORM = "instagram";

// DOM ELEMENTS
const form = document.getElementById("downloadForm");
const videoUrl = document.getElementById("videoUrl");
const message = document.getElementById("message");
const pasteButton = document.getElementById("pasteButton");
const submitButton = document.getElementById("submitBtn");
const btnText = document.getElementById("btnText");

const resultContainer = document.getElementById("resultContainer");
const thumbnail = document.getElementById("videoThumbnail");
const downloadFileBtn = document.getElementById("downloadFileBtn");

const videoTitle = document.getElementById("videoTitle");
const videoAuthor = document.getElementById("videoAuthor");
const videoDuration = document.getElementById("videoDuration");

const carouselGallery = document.getElementById("carouselGallery");

// APPLICATION STATE
let currentUrl = "";
let currentMediaType = "";
let lookupVersion = 0;


// --------------------------------------------------
// HELPERS
// --------------------------------------------------

function setMessage(text, type = "") {
    message.textContent = text;
    message.className = type
        ? `message ${type}`
        : "message";
}

function formatDuration(totalSeconds) {
    if (!totalSeconds) return "";

    const minutes = Math.floor(totalSeconds / 60);
    const seconds = String(
        Math.floor(totalSeconds % 60)
    ).padStart(2, "0");

    return `${minutes}:${seconds}`;
}

function errorText(data, fallback) {
    return data && typeof data.detail === "string"
        ? data.detail
        : fallback;
}

function setLoading(isLoading) {
    submitButton.disabled = isLoading;

    btnText.textContent = isLoading
        ? "Detecting media..."
        : "Get media information";

    const existing = document.getElementById("loadingSpinner");

    if (isLoading && !existing) {
        const spinner = document.createElement("span");
        spinner.id = "loadingSpinner";
        spinner.className = "spinner";
        submitButton.appendChild(spinner);
    } else if (!isLoading && existing) {
        existing.remove();
    }
}

function resetResult() {
    lookupVersion++;
    currentUrl = "";
    currentMediaType = "";

    resultContainer.hidden = true;

    thumbnail.hidden = true;
    thumbnail.removeAttribute("src");

    downloadFileBtn.hidden = false;
    downloadFileBtn.disabled = true;

    if (carouselGallery) {
        carouselGallery.hidden = true;
        carouselGallery.replaceChildren();
    }
}


// --------------------------------------------------
// SAVE FILE TO DEVICE
// --------------------------------------------------

function saveBlob(blob, filename) {
    const downloadUrl = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(() => {
        URL.revokeObjectURL(downloadUrl);
    }, 60000);
}


// --------------------------------------------------
// API DOWNLOAD HELPER
// --------------------------------------------------

async function fetchDownload(endpoint, payload) {
    const response = await fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));

        throw new Error(
            errorText(data, "Download failed. Try again.")
        );
    }

    return response;
}


// --------------------------------------------------
// PASTE INSTAGRAM URL
// --------------------------------------------------

pasteButton.addEventListener("click", async () => {
    try {
        videoUrl.value = await navigator.clipboard.readText();

        resetResult();
        setMessage("URL pasted.", "success");

    } catch (error) {
        setMessage(
            "Couldn't read the clipboard. Paste the URL manually.",
            "error"
        );
    }
});

videoUrl.addEventListener("input", resetResult);


// --------------------------------------------------
// DOWNLOAD INDIVIDUAL CAROUSEL ITEM
// --------------------------------------------------

async function downloadCarouselItem(item, url, button) {
    const originalLabel = button.textContent;

    button.disabled = true;
    button.textContent = "Downloading...";

    setMessage("");

    try {
        const response = await fetchDownload(
            "/api/video/carousel/item/download",
            {
                url: url,
                platform: PLATFORM,
                index: item.index
            }
        );

        const blob = await response.blob();

        const contentType = (
            response.headers.get("content-type") || ""
        ).split(";")[0].toLowerCase().trim();

        const extensions = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "video/mp4": "mp4"
        };

        const extension = extensions[contentType];

        if (!extension) {
            throw new Error(
                "Unsupported media format returned by server."
            );
        }

        const filename =
            `instagram-item-${item.index}.${extension}`;

        saveBlob(blob, filename);

        setMessage(
            `Download started for item ${item.index}.`,
            "success"
        );

    } catch (error) {
        console.error("Carousel download error:", error);

        setMessage(
            error.message || "Unable to download this item.",
            "error"
        );

    } finally {
        button.disabled = false;
        button.textContent = originalLabel;
    }
}


// --------------------------------------------------
// RENDER CAROUSEL GALLERY
// --------------------------------------------------

function renderCarousel(items, url) {
    if (!carouselGallery) {
        throw new Error(
            "Carousel gallery container is missing from index.html."
        );
    }

    if (!Array.isArray(items) || items.length === 0) {
        throw new Error(
            "Carousel detected, but no individual items were returned."
        );
    }

    carouselGallery.replaceChildren();

    for (const item of items) {
        const card = document.createElement("div");
        card.className = "carousel-item";

        // Preview image
        const image = document.createElement("img");

        image.src = item.thumbnail;
        image.alt = `Instagram carousel item ${item.index}`;
        image.loading = "lazy";
        image.referrerPolicy = "no-referrer";

        // Media label
        const itemLabel = document.createElement("p");
        itemLabel.className = "carousel-item-label";

        itemLabel.textContent =
            item.media_type === "video"
                ? `Video ${item.index}`
                : `Photo ${item.index}`;

        // Individual download button
        const downloadButton = document.createElement("button");

        downloadButton.type = "button";
        downloadButton.className = "download-btn carousel-download-btn";

        downloadButton.textContent =
            item.media_type === "video"
                ? "Download video (.mp4)"
                : "Download photo";

        downloadButton.addEventListener("click", () => {
            downloadCarouselItem(
                item,
                url,
                downloadButton
            );
        });

        card.appendChild(image);
        card.appendChild(itemLabel);
        card.appendChild(downloadButton);

        carouselGallery.appendChild(card);
    }

    carouselGallery.hidden = false;
}


// --------------------------------------------------
// DETECT INSTAGRAM MEDIA
// --------------------------------------------------

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const url = videoUrl.value.trim();

    if (!url) {
        setMessage(
            "Paste an Instagram URL first.",
            "error"
        );
        return;
    }

    resetResult();
    const thisLookup = lookupVersion;

    setLoading(true);
    setMessage("");

    try {
        const response = await fetch("/api/video/info", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: url,
                platform: PLATFORM
            })
        });

        const data = await response.json().catch(() => ({}));

        // Ignore results from URLs the user has changed
        if (thisLookup !== lookupVersion) return;

        if (!response.ok) {
            throw new Error(
                errorText(
                    data,
                    "Unable to retrieve Instagram media."
                )
            );
        }

        console.log("MEDIA DETECTION:", data);

        const mediaType = data.media_type;

        if (!["photo", "video", "carousel"].includes(mediaType)) {
            throw new Error(
                "Unsupported Instagram media type."
            );
        }

        currentUrl = url;
        currentMediaType = mediaType;

        const mediaLabels = {
            photo: "Instagram photo",
            video: "Instagram video",
            carousel: "Instagram carousel"
        };

        // Media information
        videoTitle.textContent =
            data.title || mediaLabels[mediaType];

        videoAuthor.textContent = data.author
            ? `By ${data.author}`
            : "";

        videoDuration.textContent =
            mediaType === "video" && data.duration
                ? `Duration: ${formatDuration(data.duration)}`
                : "";

        // Main preview
        thumbnail.hidden = true;

        if (data.thumbnail) {
            thumbnail.onload = () => {
                thumbnail.hidden = false;
            };

            thumbnail.onerror = () => {
                thumbnail.hidden = true;
            };

            thumbnail.src = data.thumbnail;
        }

        // DIFFERENT MEDIA TYPES
        if (mediaType === "carousel") {
            // Hide the single-file download button
            downloadFileBtn.hidden = true;

            // Show individual carousel items
            renderCarousel(
                data.carousel_items,
                url
            );

            setMessage(
                `${data.carousel_items.length} carousel items detected.`,
                "success"
            );

        } else {
            // Single photo or video
            downloadFileBtn.hidden = false;
            downloadFileBtn.disabled = false;

            downloadFileBtn.textContent =
                mediaType === "photo"
                    ? "Download photo (.jpg)"
                    : "Download video (.mp4)";

            setMessage(
                `${mediaLabels[mediaType]} detected successfully.`,
                "success"
            );
        }

        resultContainer.hidden = false;

    } catch (error) {
        if (thisLookup === lookupVersion) {
            resetResult();
            setMessage(error.message, "error");
        }

    } finally {
        if (thisLookup === lookupVersion) {
            setLoading(false);
        }
    }
});


// --------------------------------------------------
// DOWNLOAD SINGLE PHOTO / VIDEO
// --------------------------------------------------

downloadFileBtn.addEventListener("click", async () => {
    if (
        !currentUrl ||
        !["photo", "video"].includes(currentMediaType)
    ) {
        setMessage(
            "Detect a photo or video first.",
            "error"
        );
        return;
    }

    // Unified endpoint automatically selects the downloader
    const endpoint = "/api/video/download";

    const filename = currentMediaType === "photo"
        ? "instagram-photo.jpg"
        : "instagram-video.mp4";

    const originalLabel = downloadFileBtn.textContent;

    downloadFileBtn.disabled = true;
    downloadFileBtn.textContent = "Downloading...";

    setMessage("");

    try {
        const response = await fetchDownload(
            endpoint,
            {
                url: currentUrl,
                platform: PLATFORM
            }
        );

        const blob = await response.blob();

        saveBlob(blob, filename);

        setMessage(
            "Download started successfully.",
            "success"
        );

    } catch (error) {
        console.error("Media download error:", error);

        setMessage(
            error.message || "Download failed.",
            "error"
        );

    } finally {
        downloadFileBtn.disabled = false;
        downloadFileBtn.textContent = originalLabel;
    }
});

// Initial state
resetResult();
