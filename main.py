from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
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

def remove_files(*file_paths):
    """Função para limpar os arquivos temporários após o envio do vídeo."""
    for path in file_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

@app.post("/cut")
def cut_video(data: CutRequest, background_tasks: BackgroundTasks):
    request_id = str(uuid.uuid4())
    input_file = f"input_{request_id}.mp4"
    output_file = f"output_{request_id}.mp4"

    try:
        # 1. Baixar o vídeo da URL
        response = requests.get(data.video_url, stream=True)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Erro ao baixar o vídeo da URL fornecida.")
        
        with open(input_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                f.write(chunk)

        # 2. Fazer o corte ultra-rápido com FFmpeg
        command = [
            "ffmpeg",
            "-ss", data.start_time,
            "-to", data.end_time,
            "-i", input_file,
            "-c", "copy",
            "-y",
            output_file
        ]

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            remove_files(input_file)
            raise HTTPException(status_code=500, detail=f"Erro no FFmpeg: {result.stderr.decode()}")

        # Clean up do arquivo de entrada imediatamente
        remove_files(input_file)

        # Agendar a exclusão do arquivo cortado APÓS ele ser enviado ao n8n
        background_tasks.add_task(remove_files, output_file)

        # 3. Retornar o arquivo MP4 diretamente para o n8n
        return FileResponse(
            path=output_file,
            media_type="video/mp4",
            filename=f"corte_{request_id}.mp4"
        )

    except Exception as e:
        remove_files(input_file, output_file)
        raise e