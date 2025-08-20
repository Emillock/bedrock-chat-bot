import json
import logging
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langchain.schema import BaseMessage

from src.models.predict_model import main as predict_main
from src.utils import get_response_stream, retrieve_and_generate_stream

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BAKU_TZ = timezone(timedelta(hours=4))

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Backend server for ML project",
    description="REST API for ML project",
    version="1.0.0",
    docs_url="/docs",
)

# Add CORS middleware to allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Data(BaseModel):
    prompt: str
    modelName: str
    system: str
    temperature: float
    maxTokens: int

@app.get("/health")
def health() -> Dict[str, Any]:
    utc_time = datetime.now(timezone.utc).isoformat()
    baku_time = datetime.now(BAKU_TZ).isoformat()
    return {"status": "healthy", "utc_time": utc_time, "baku_time": baku_time}


@app.post("/generate")
async def generate(data: Data):
    start_time = datetime.now()
    prompt = data.prompt
    model_name = data.modelName
    system= data.system
    temperature = data.temperature
    max_tokens = data.maxTokens
    try:
        print(f"Received prompt: {prompt} for model: {model_name} with temperature {temperature} and max_tokens: {max_tokens}", flush=True)

    except HTTPException:
        # pass through expected client errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Internal server error during prediction: {str(e)}"
        )
    for chunk in retrieve_and_generate_stream(
        model_name=model_name,
        user_query=prompt,
    ):
        print(chunk, flush=True) 
    
    return StreamingResponse(
        get_response_stream(
            prompt=prompt,
            model_name=model_name,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
        media_type="text/event-stream")