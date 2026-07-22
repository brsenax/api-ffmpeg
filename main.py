import os
import shutil
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="API FFmpeg Video Cutter")

class CutSegment(BaseModel):
    start_time: str
    end_time: str
    output_name: Optional[str] = "corte.mp4"

class ProcessVideoRequest(BaseModel):
    video_url: Optional[str] = None
    file_path: Optional[str] = "/tmp/video_original.mp4"
    segments: List[CutSegment]

@app.get("/")
def read_root():
    return {"status": "online", "message": "API FFmpeg pronta para processar cortes!"}

@app.post("/cut")
def cut_video(data: ProcessVideoRequest):
    input_file = data.file_path

    # Se uma URL direta de MP4 for informada, faz o download para a pasta /tmp
    if data.video_url and data.video_url.startswith("http"):
        input_file = "/tmp/downloaded_video.mp4"
        try:
            response = requests.get(data.video_url, stream=True)
            response.raise_for_status()
            with open(input_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao baixar o vídeo: {str(e)}")

    if not os.path.exists(input_file):
        raise HTTPException(status_code=404, detail=f"Arquivo de vídeo não encontrado em: {input_file}")

    processed_files = []

    for idx, segment in enumerate(data.segments):
        output_filename = f"/tmp/corte_{idx + 1}.mp4"
        
        # Comando FFmpeg otimizado para corte rápido sem re-encoding pesado
        command = [
            "ffmpeg", "-y",
            "-ss", segment.start_time,
            "-to", segment.end_time,
            "-i", input_file,
            "-c", "copy",
            output_filename
        ]

        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processed_files.append(output_filename)
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"Erro ao cortar trecho {segment.start_time}-{segment.end_time}: {e.stderr.decode('utf-8')}")

    return {
        "message": "Cortes realizados com sucesso!",
        "files": processed_files
    }