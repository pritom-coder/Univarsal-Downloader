# Multi-site Video Downloader

## Setup

1. Install Python 3.13+
2. Install dependencies:
   pip install -r backend/requirements.txt
   
   Also download ffmpeg from here - https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip

   Setup for ffmpeg :
   1. create a folder on your localdisk name it ffmpeg
   2. extrat the file in the ffmpeg folder 
   3. run all the exe files

3. Run FastAPI server:
   uvicorn backend.main:app --reload

4. Open frontend/index.html in browser
5. Paste video URL → Click Download
