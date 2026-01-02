async function checkVideo() {
  const videoURL = document.getElementById("videoURL").value.trim();
  const statusEl = document.getElementById("status");
  const checkBtn = document.getElementById("checkBtn");
  const infoSection = document.getElementById("videoInfoSection");
  const qualitySelect = document.getElementById("qualitySelect");

  if (!videoURL) {
    statusEl.textContent = "⚠️ Please paste a link!";
    statusEl.className = "error";
    return;
  }

  statusEl.textContent = "🔍 Fetching qualities...";
  statusEl.className = "loading";
  checkBtn.disabled = true;
  infoSection.style.display = "none";

  try {
    const response = await fetch("http://127.0.0.1:8000/info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: videoURL }),
    });

    if (!response.ok) throw new Error("Video not found or link invalid.");

    const data = await response.json();
    
    // টাইটেল সেট করা
    document.getElementById("videoTitle").textContent = "🎬 " + data.title;
    
    // অপশনগুলো লোড করা
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
    statusEl.textContent = "❌ " + err.message;
    statusEl.className = "error";
  } finally {
    checkBtn.disabled = false;
  }
}

async function downloadVideo() {
  const videoURL = document.getElementById("videoURL").value;
  const quality = document.getElementById("qualitySelect").value;
  const statusEl = document.getElementById("status");
  const btn = document.getElementById("downloadBtn");

  statusEl.textContent = "⏳ Downloading file to server...";
  statusEl.className = "loading";
  btn.disabled = true;

  try {
    const response = await fetch("http://127.0.0.1:8000/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: videoURL, quality: quality }),
    });

    const data = await response.json();
    if (response.ok) {
      statusEl.textContent = "✅ Success: " + data.filename;
      statusEl.className = "success";
    } else {
      throw new Error(data.detail || "Download failed");
    }
  } catch (err) {
    statusEl.textContent = "❌ Error: " + err.message;
    statusEl.className = "error";
  } finally {
    btn.disabled = false;
  }
}