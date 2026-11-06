const form = document.getElementById("downloadForm");
const videoUrl = document.getElementById("videoUrl");
const message = document.getElementById("message");
const pasteButton = document.getElementById("pasteButton");


let selectedPlatform = "youtube";

//Platform selection
document.querySelectorAll(".platform").forEach(button => {

    button.addEventListener("click", () => {

        document.querySelectorAll(".platform").forEach(item => {
            item.classList.remove("active");
        });

        button.classList.add("active");

        selectedPlatform = button.dataset.platform;

        videoUrl.placeholder =
            selectedPlatform === "youtube"
            ? "https://www.youtube.com/..."
            : "https://www.instagram.com/...";

        message.textContent = "";
    });
});

//Paste URL
pasteButton.addEventListener("click", async () => {

    try {
        const text = await navigator.clipboard.readText();

        videoUrl.value = text;

        message.textContent = "URL pasted successfully";
    } catch (error) {
        message.textContent = 
            "Please paste the URL manually.";
    }
});

//submit URL
form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const url = videoUrl.value.trim();
    const submitButton = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");
    const resultContainer = document.getElementById("resultContainer");

    if (!url) {
        message.textContent = "Please enter a video URL.";
        return;
    }

    // Activate loading state with spinner
    submitButton.disabled = true;
    btnText.textContent = "Fetching info...";
    
    // Add spinner element if it doesn't exist yet
    if (!document.getElementById("loadingSpinner")) {
        const spinner = document.createElement("span");
        spinner.id = "loadingSpinner";
        spinner.className = "spinner";
        submitButton.appendChild(spinner);
    }

    message.textContent = "";
    resultContainer.style.display = "none";

    try {
        const response = await fetch("/api/video/info", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: url,
                platform: selectedPlatform
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to fetch video info");
        }

        // Populate preview card fields
        document.getElementById("videoThumbnail").src = data.thumbnail || "";
        document.getElementById("videoTitle").textContent = data.title || "Untitled Video";
        document.getElementById("videoAuthor").textContent = "Channel: " + (data.author || "Unknown");
        document.getElementById("videoDuration").textContent = "Duration: " + (data.duration ? data.duration + " seconds" : "N/A");
        
        resultContainer.style.display = "flex";

        // Wire up the download button inside the preview card
        const downloadFileBtn = document.getElementById("downloadFileBtn");
        if (downloadFileBtn) {
            downloadFileBtn.onclick = async () => {
                downloadFileBtn.disabled = true;
                downloadFileBtn.textContent = "Downloading...";
                
                await handleDownload(url, selectedPlatform);
                
                downloadFileBtn.disabled = false;
                downloadFileBtn.textContent = "Download Video (.mp4)";
            };
        }

        message.style.color = "#34d399";
        message.textContent = "Success! Video ready.";

    } catch (error) {
        message.style.color = "#f87171";
        message.textContent = error.message;
        resultContainer.style.display = "none";
    } finally {
        // Reset button state
        submitButton.disabled = false;
        btnText.textContent = "Get video information";
        const spinner = document.getElementById("loadingSpinner");
        if (spinner) spinner.remove();
    }
});

// Download handler function
async function handleDownload(url, platform){
    try {
        const response = await fetch("/api/video/download", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({url, platform})
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Download failed");
        }

        // Convert response to a blob and trigger browser download
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = "video.mp4";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
        alert("Error: " + error.message)
    }
}