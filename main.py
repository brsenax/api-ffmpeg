from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import uuid
import os
import yt_dlp

app = FastAPI()

class CutRequest(BaseModel):
    video_url: str
    start_time: str
    end_time: str

def get_direct_stream_url(url: str) -> str:
    """Extrai a URL direta de streaming se for um link do YouTube,

    caso contrário, retorna a própria URL recebida.
    """
    if "youtube.com" in url or "youtu.be" in url:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return info['url']
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Erro ao processar link do YouTube: {str(e)}")
    return url

@app.post("/cut")
async def cut_video(request: CutRequest):
    # Generates a unique output filename
    output_filename = f"corte_{uuid.uuid4()}.mp4"
    output_path = os.path.join("/tmp", output_filename)

    # 1. Resolve a URL (YouTube ou link direto de MP4)
    direct_url = get_direct_stream_url(request.video_url)

    # 2. Comando otimizado do FFmpeg
    command = [
        "ffmpeg",
        "-ss", request.start_time,
        "-to", request.end_time,
        "-i", direct_url,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-strict", "experimental",
        "-y",
        output_path
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=output_filename
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro no FFmpeg: {e.stderr.decode('utf-8')}"
        )