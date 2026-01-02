import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp
from urllib.parse import quote

app = FastAPI()

# CORS settings jate frontend theke request block na hoy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Filename"],
)

# Render-er temporary file storage (tmp folder use kora hoy)
TEMP_DIR = "/tmp/downloads"
os.makedirs(TEMP_DIR, exist_ok=True)

# Cookies file-er path (backend folder-ei thakbe)
COOKIE_PATH = os.path.join(os.path.dirname(__file__), "cookies.txt")

class VideoRequest(BaseModel):
    url: str
    quality: str = "best"

def cleanup_file(path: str):
    """Download hoye jawar por file muche fele jate server space ful na hoy"""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Cleanup error: {e}")

@app.get("/health")
def health_check():
    return {"status": "running"}

@app.post("/info")
async def get_video_info(request: VideoRequest):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'cookiefile': COOKIE_PATH if os.path.exists(COOKIE_PATH) else None,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            formats = info.get('formats', [])
            
            qualities = []
            seen = set()
            for f in formats:
                h = f.get('height')
                # Sudhu video shoho formats gulo nibe
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
    
    # Format selection logic
    if quality == "audio":
        format_str = 'bestaudio/best'
    else:
        # Quality merge korar jonno bestvideo+bestaudio format
        format_str = f'bestvideo[height<={quality}]+bestaudio/best/best[height<={quality}]'
    
    ydl_opts = {
        'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
        'format': format_str,
        'cookiefile': COOKIE_PATH if os.path.exists(COOKIE_PATH) else None,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            filename = os.path.basename(file_path)
            
        # Download shesh hole background-e file delete korar task add kora
        background_tasks.add_task(cleanup_file, file_path)
        
        # FileResponse die file-ti user-er browser-e pathano
        return FileResponse(
            path=file_path, 
            filename=filename, 
            headers={"X-Filename": quote(filename)}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Frontend serve logic (Static files)
# root directory theke frontend folder ta serve korbe
current_dir = os.path.dirname(__file__)
frontend_path = os.path.normpath(os.path.join(current_dir, "..", "frontend"))

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
