import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp
from urllib.parse import quote

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Filename"],
)

# Render temporary directory
TEMP_DIR = "/tmp/downloads"
os.makedirs(TEMP_DIR, exist_ok=True)

class VideoRequest(BaseModel):
    url: str
    quality: str = "best"

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.post("/info")
async def get_video_info(request: VideoRequest):
    # 'backend/cookies.txt' file thakle eita kaj korbe
    cookie_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
    ydl_opts = {
        'quiet': True, 
        'noplaylist': True,
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            formats = info.get('formats', [])
            qualities = [{"label": f"{f.get('height')}p", "value": str(f.get('height'))} 
                         for f in formats if f.get('height') and f.get('vcodec') != 'none']
            
            # Unique qualities filter
            unique_qualities = list({q['value']: q for q in qualities}.values())
            unique_qualities.sort(key=lambda x: int(x['value']), reverse=True)
            unique_qualities.append({"label": "Audio (MP3)", "value": "audio"})
            
            return {"title": info.get('title'), "qualities": unique_qualities}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/download")
async def download_video(request: VideoRequest, background_tasks: BackgroundTasks):
    cookie_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
    format_str = 'bestaudio/best' if request.quality == "audio" else f'bestvideo[height<={request.quality}]+bestaudio/best'
    
    ydl_opts = {
        'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
        'format': format_str,
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            file_path = ydl.prepare_filename(info)
            filename = os.path.basename(file_path)
            
        background_tasks.add_task(cleanup_file, file_path)
        return FileResponse(path=file_path, filename=filename, headers={"X-Filename": quote(filename)})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Frontend serve
current_dir = os.path.dirname(__file__)
frontend_path = os.path.join(current_dir, "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
