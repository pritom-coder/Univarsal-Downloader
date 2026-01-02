from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel
import yt_dlp
import os
from dotenv import load_dotenv

# Load configuration from .env file
load_dotenv()

# Set up global variables from environment or defaults
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
DEBUG = os.getenv("DEBUG", "False") == "True"

# Ensure the download directory exists on the system
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Initialize FastAPI application
app = FastAPI()

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your frontend (HTML/JS) to communicate with this backend API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your specific domain      
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the data structure for incoming requests
class VideoRequest(BaseModel):
    url: str
    quality: str = "best" # Default to 'best' if no quality is provided

# ROUTE 1: Fetch Video Information and available qualities
@app.post("/info")
def get_video_info(request: VideoRequest):
    url = request.url
    
    # Configuration for yt_dlp to extract info without downloading
    ydl_opts = {
        'quiet': True,       # Suppress unnecessary terminal output
        'noplaylist': True,  # Process only the single video link provided
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract metadata without downloading the actual file
            info = ydl.extract_info(url, download=False)
            
            formats = info.get('formats', [])
            available_qualities = set() # Using a set to avoid duplicate resolutions

            # Loop through available formats to find valid video heights
            for f in formats:
                if f.get('height'):
                    available_qualities.add(f['height'])
            
            # Sort resolutions from highest to lowest (e.g., 1080p, 720p...)
            sorted_qualities = sorted(list(available_qualities), reverse=True)
            
            # Map resolutions to a cleaner format for the frontend dropdown
            options = [{"label": f"{q}p", "value": str(q)} for q in sorted_qualities]
            
            # Always add an option for audio-only download
            options.append({"label": "Audio Only (MP3)", "value": "audio"})

            return {
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "qualities": options
            }

    except Exception as e:
        # Return a 400 error if URL is invalid or info extraction fails
        raise HTTPException(status_code=400, detail=str(e))

# ROUTE 2: Handle the actual video/audio download
@app.post("/download")
def download_video(request: VideoRequest):
    url = request.url
    quality = request.quality
    
    # Set the download format based on user selection
    if quality == "audio":
        format_string = 'bestaudio/best' # Get best audio only
    elif quality == "best":
         format_string = 'bestvideo+bestaudio/best' # Get maximum quality
    else:
        # Target specific resolution height or the next best thing below it
        format_string = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
    
    # Download settings
    ydl_opts = {
        # Define where to save the file and what to name it
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'format': format_string,
        'noplaylist': True,  
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download the file to the local server storage
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        return {
            "title": info.get('title'), 
            "filename": filename, 
            "quality_downloaded": quality,
            "status": "completed"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))