import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp
from urllib.parse import quote

app = FastAPI()

# CORS settings: Render-এ হোস্ট করলে এটি অবশ্যই লাগবে
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Filename"],
)

# Render-এর জন্য অস্থায়ী ফোল্ডার
TEMP_DIR = "/tmp/downloads" if os.environ.get("RENDER") else "temp_downloads"
os.makedirs(TEMP_DIR, exist_ok=True)

class VideoRequest(BaseModel):
    url: str
    quality: str = "best"

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/info")
async def get_video_info(request: VideoRequest):
    ydl_opts = {'quiet': True, 'noplaylist': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            formats = info.get('formats', [])
            qualities = []
            seen = set()
            for f in formats:
                h = f.get('height')
                if h and h not in seen and f.get('vcodec') != 'none':
                    qualities.append({"label": f"{h}p", "value": str(h)})
                    seen.add(h)
            qualities.sort(key=lambda x: int(x['value']), reverse=True)
            qualities.append({"label": "Audio (MP3)", "value": "audio"})
            return {"title": info.get('title'), "qualities": qualities}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/download")
async def download_video(request: VideoRequest, background_tasks: BackgroundTasks):
    url = request.url
    quality = request.quality
    
    format_str = 'bestaudio/best' if quality == "audio" else f'bestvideo[height<={quality}]+bestaudio/best/best[height<={quality}]'
    
    ydl_opts = {
        'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
        'format': format_str,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            filename = os.path.basename(file_path)
            
        # ফাইলটি পাঠানোর পর সার্ভার থেকে মুছে ফেলার ব্যবস্থা
        background_tasks.add_task(cleanup_file, file_path)
        
        return FileResponse(
            path=file_path, 
            filename=filename, 
            headers={"X-Filename": quote(filename)}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Frontend files serve করা
current_dir = os.path.dirname(__file__)
frontend_path = os.path.join(current_dir, "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
