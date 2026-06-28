from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import tempfile
import os
import glob

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/subtitle")
async def get_subtitle(req: DownloadRequest):
    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['zh-Hans', 'zh', 'en', 'zh-Hant'],
            'subtitlesformat': 'vtt/srt/best',
            'convertsubtitles': 'srt',
            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(req.url, download=True)
                title = info.get('title', 'Video')
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        srt_files = glob.glob(os.path.join(tmpdir, '*.srt'))
        vtt_files = glob.glob(os.path.join(tmpdir, '*.vtt'))
        sub_file = srt_files + vtt_files

        if not sub_file:
            raise HTTPException(status_code=404, detail="No subtitle found")

        with open(sub_file[0], 'r', encoding='utf-8') as f:
            content = f.read()

        return {"title": title, "content": content}
