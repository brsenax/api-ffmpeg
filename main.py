from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import requests
import os
import uuid

app = FastAPI()

class CutRequest(BaseModel):
    video_url: str
    start_time: str
    end_time: str

@app.post("/cut")
def cut_video(data: CutRequest):
    request_id = str(uuid.uuid4())
    input_file = f"input_{request_id}.mp4"
    output_file = f"output_{request_id}.mp4"

    try:
        # 1. Baixar o vídeo da URL enviada pelo n8n
        response = requests.get(data.video_url, stream=True)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Erro ao baixar o vídeo da URL fornecida.")
        
        with open(input_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                f.write(chunk)

        # 2. Executar o FFmpeg para fazer o corte exato de forma ultra-rápida
        command = [
            "ffmpeg",
            "-ss", data.start_time,
            "-to", data.end_time,
            "-i", input_file,
            "-c", "copy",  # Copia os streams de áudio/vídeo sem reprocessar (corte instantâneo)
            "-y",
            output_file
        ]

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erro no FFmpeg: {result.stderr.decode()}")

        # Sucesso! Em produção aqui retornamos o arquivo ou fazemos o upload.
        return {
            "status": "success",
            "message": "Vídeo cortado com sucesso!",
            "output_file": output_file
        }

    finally:
        # Limpar o arquivo de entrada temporário da memória do servidor
        if os.path.exists(input_file):
            os.remove(input_file)