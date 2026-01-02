async function checkVideo() {
    const videoURL = document.getElementById("videoURL").value.trim();
    const statusEl = document.getElementById("status");
    const infoSection = document.getElementById("videoInfoSection");
    const qualitySelect = document.getElementById("qualitySelect");

    if (!videoURL) {
        statusEl.textContent = "⚠️ Please paste a link!";
        return;
    }

    statusEl.textContent = "🔍 Fetching video info...";
    infoSection.style.display = "none";

    try {
        const response = await fetch("/info", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: videoURL }),
        });

        if (!response.ok) throw new Error("Could not find video!");

        const data = await response.json();
        document.getElementById("videoTitle").textContent = data.title;
        
        qualitySelect.innerHTML = "";
        data.qualities.forEach(q => {
            const opt = document.createElement("option");
            opt.value = q.value;
            opt.textContent = q.label;
            qualitySelect.appendChild(opt);
        });

        statusEl.textContent = "";
        infoSection.style.display = "block";
    } catch (err) {
        statusEl.textContent = "❌ Error: " + err.message;
    }
}

async function downloadVideo() {
    const videoURL = document.getElementById("videoURL").value;
    const quality = document.getElementById("qualitySelect").value;
    const statusEl = document.getElementById("status");

    statusEl.textContent = "⏳ Downloading to server... please wait";

    try {
        const response = await fetch("/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: videoURL, quality: quality }),
        });

        if (!response.ok) throw new Error("Download failed!");

        const blob = await response.blob();
        let filename = "video.mp4";
        const customHeader = response.headers.get("X-Filename");
        if (customHeader) filename = decodeURIComponent(customHeader);

        // ব্রাউজারের মাধ্যমে ইউজারের ডাউনলোড ফোল্ডারে পাঠানো
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        a.remove();
        
        statusEl.textContent = "✅ Download Complete!";
    } catch (err) {
        statusEl.textContent = "❌ Error: " + err.message;
    }
}
