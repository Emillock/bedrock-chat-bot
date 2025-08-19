import logging
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.models.predict_model import main as predict_main

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


@app.get("/health")
def health() -> Dict[str, Any]:
    utc_time = datetime.now(timezone.utc).isoformat()
    baku_time = datetime.now(BAKU_TZ).isoformat()
    return {"status": "healthy", "utc_time": utc_time, "baku_time": baku_time}


@app.post("/predict")
async def predict(file: UploadFile = File(...)) -> Dict[str, Any]:
    start_time = datetime.now()
    try:
        # Validate file type
        suffix = Path(file.filename).suffix.lower()
        if suffix not in {".csv", ".xlsx", ".xls", ".parquet"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Please upload CSV or Excel files only.",
            )

        # Read file content (async!)
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        logger.info(f"Processing file: {file.filename} ({len(file_content)} bytes)")

        # Generate predictions
        predictions_list = predict_main(file_content, filename=file.filename)

        # Ensure JSON-serializable (handles numpy arrays/Series)
        try:
            predictions_list = list(predictions_list)
        except TypeError:
            predictions_list = [p for p in predictions_list]

        processing_time = (datetime.now() - start_time).total_seconds()
        return {
            "status": "success",
            "message": "Predictions generated successfully",
            "data": {
                "predictions": predictions_list,
                "num_predictions": len(predictions_list),
                "processing_time_seconds": round(processing_time, 3),
            },
        }

    except HTTPException:
        # pass through expected client errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Internal server error during prediction: {str(e)}"
        )
