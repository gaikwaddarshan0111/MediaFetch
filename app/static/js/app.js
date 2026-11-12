
const PLATFORM = "instagram";

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

let currentUrl = "";
let currentMediaType = "";

function setMessage(text, type = "") {
    message.textContent = text;
    message.className = type ? "message " + type : "message";
}

function formatDuration(totalSeconds) {
    if (!totalSeconds) return "";

    const minutes = Math.floor(totalSeconds / 60);
    const seconds = String(Math.floor(totalSeconds % 60).padStart(2, "0"));

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
    currentUrl = "";
    currentMediaType = "";
    resultContainer.hidden = true;
    thumbnail.hidden = true;
    thumbnail.removeAttribute("src");
}

// Paste URL from clipboard
pasteButton.addEventListener("click", async () => {
    try {
        videoUrl.value = await navigator.clipboard.readText();
        resetResult();
        setMessage("URL pasted.", "success");
    } catch (error) {
        setMessage(
            "Couldn't read the clipboard. Paste the link manually.",
            "error"
        );
    }
});

// Reset stale metadata when URL changes
videoUrl.addEventListener("input", resetResult);

// Automatically detect Instagram media
form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const url = videoUrl.value.trim();

    if (!url) {
        setMessage("Paste an Instagram link first.", "error");
        return;
    }

    resetResult();
    setLoading(true);
    setMessage("");

    try {
        const response = await fetch("/api/video/info", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url,
                platform: PLATFORM
            })
        });

        const data = await response.json().catch(() => ({}));

        console.log("========== MEDIA DETECTION ==========");
        console.log("Full API response:", data);
        console.log("Detected media type:", data.media_type);
        console.log("Download format:", data.download_format);

        if (!response.ok) {
            throw new Error(
                errorText(data, "Unable to retrieve Instagram media.")
            );
        }

        const mediaType = data.media_type;

        if (!["photo", "video", "carousel"].includes(mediaType)) {
            throw new Error("Unsupported Instagram media type.");
        }

        currentUrl = url;
        currentMediaType = mediaType;

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

        const mediaLabel = {
            photo: "Instagram photo",
            video: "Instagram video",
            carousel: "Instagram carousel"
        };

        videoTitle.textContent =
            data.title || mediaLabel[mediaType];

        videoAuthor.textContent = data.author
            ? `By ${data.author}`
            : "";

        videoDuration.textContent =
            mediaType === "video" && data.duration
                ? `Duration: ${formatDuration(data.duration)}`
                : "";

        const downloadLabels = {
            photo: "Download photo (.jpg)",
            video: "Download video (.mp4)",
            carousel: "Carousel download coming soon"
        };

        downloadFileBtn.textContent = downloadLabels[mediaType];
        downloadFileBtn.disabled = mediaType === "carousel";

        resultContainer.hidden = false;

        setMessage(
            `${mediaLabel[mediaType]} detected successfully.`,
            "success"
        );

    } catch (error) {
        setMessage(error.message, "error");
    } finally {
        setLoading(false);
    }
});

// Download detected media
downloadFileBtn.addEventListener("click", async () => {
    if (!currentUrl || !["photo", "video"].includes(currentMediaType)) {
        setMessage("Detect a supported Instagram post first.", "error");
        return;
    }

    const endpoint = currentMediaType === "photo"
        ? "/api/video/photo/download"
        : "/api/video/download";

    console.log("Detected type:", currentMediaType);
    console.log("Download endpoint:", endpoint);

    const filename = currentMediaType === "photo"
        ? "instagram-photo.jpg"
        : "instagram-video.mp4";

    const originalLabel = downloadFileBtn.textContent;

    downloadFileBtn.disabled = true;
    downloadFileBtn.textContent = "Downloading...";
    setMessage("");

    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: currentUrl,
                platform: PLATFORM
            })
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));

            throw new Error(
                errorText(data, "Download failed. Try again.")
            );
        }

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = downloadUrl;
        link.download = filename;

        document.body.appendChild(link);
        link.click();
        link.remove();

        // Allow browser time to initiate the download
        setTimeout(() => {
            URL.revokeObjectURL(downloadUrl);
        }, 60000);

        setMessage("Download started successfully.", "success");

    } catch (error) {
        setMessage(error.message, "error");
    } finally {
        downloadFileBtn.disabled = false;
        downloadFileBtn.textContent = originalLabel;
    }
});
