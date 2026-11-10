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

let currentUrl = "";

function setMessage(text, type = "") {
    message.textContent = text;
    message.className = type ? "message " + type : "message";
}

function formatDuration(totalSeconds) {
    if (!totalSeconds) return "";
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = String(Math.floor(totalSeconds % 60)).padStart(2, "0");
    return minutes + ":" + seconds;
}

function errorText(data, fallback) {
    // FastAPI returns a string for our errors and a list for validation errors
    return data && typeof data.detail === "string" ? data.detail : fallback;
}

function setLoading(isLoading) {
    submitButton.disabled = isLoading;
    btnText.textContent = isLoading ? "Fetching info..." : "Get video information";

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

// Paste URL from clipboard
pasteButton.addEventListener("click", async () => {
    try {
        videoUrl.value = await navigator.clipboard.readText();
        setMessage("URL pasted.", "success");
    } catch (error) {
        setMessage("Couldn't read the clipboard. Paste the link manually.", "error");
    }
});

// Look up video info
form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const url = videoUrl.value.trim();
    if (!url) {
        setMessage("Paste an Instagram link first.", "error");
        return;
    }

    setLoading(true);
    setMessage("");
    resultContainer.hidden = true;

    try {
        const response = await fetch("/api/video/info", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url, platform: PLATFORM })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(errorText(data, "That doesn't look like a valid Instagram link."));
        }

        currentUrl = url;

        // Thumbnails can fail (expired or blocked links): hide the image instead of showing a broken icon
        thumbnail.hidden = true;
        if (data.thumbnail) {
            thumbnail.onload = () => { thumbnail.hidden = false; };
            thumbnail.onerror = () => { thumbnail.hidden = true; };
            thumbnail.src = data.thumbnail;
        }

        document.getElementById("videoTitle").textContent = data.title || "Untitled video";
        document.getElementById("videoAuthor").textContent = data.author ? "By " + data.author : "";
        document.getElementById("videoDuration").textContent =
            data.duration ? "Duration: " + formatDuration(data.duration) : "";

        resultContainer.hidden = false;
        setMessage("Video found.", "success");
    } catch (error) {
        setMessage(error.message, "error");
    } finally {
        setLoading(false);
    }
});

// Download the video file
downloadFileBtn.addEventListener("click", async () => {
    downloadFileBtn.disabled = true;
    downloadFileBtn.textContent = "Downloading...";
    setMessage("");

    try {
        const response = await fetch("/api/video/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: currentUrl, platform: PLATFORM })
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(errorText(data, "Download failed. Try again."));
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = downloadUrl;
        link.download = "instagram-video.mp4";
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(downloadUrl);

        setMessage("Download started.", "success");
    } catch (error) {
        setMessage(error.message, "error");
    } finally {
        downloadFileBtn.disabled = false;
        downloadFileBtn.textContent = "Download video (.mp4)";
    }
});