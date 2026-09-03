from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any

from app.analysis.schemas import (
    DatasetValidationResult,
    ValidatePayloadRequest,
    SampleDatasetItem,
)
from app.analysis.validator import (
    parse_file_content,
    validate_merchant_dataset,
    get_session_data,
)
from app.analysis.samples import get_sample_datasets

router = APIRouter(prefix="/api/analysis", tags=["merchant-analysis"])

@router.get("/sample-datasets", response_model=List[SampleDatasetItem])
def list_sample_datasets():
    """Returns curated merchant sample datasets for 1-click evaluation."""
    return get_sample_datasets()

@router.post("/upload", response_model=DatasetValidationResult)
async def upload_merchant_dataset(file: UploadFile = File(...)):
    """
    Accepts an uploaded merchant dataset file (CSV, JSON, JSONL),
    validates against Sentinel's merchant schema, enforces anti-leakage guards,
    and returns a structured validation dossier in an isolated session workspace.
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        records, file_format, parse_errors = parse_file_content(content, file.filename or "dataset.csv")
        result = validate_merchant_dataset(
            records=records,
            filename=file.filename or "dataset.csv",
            file_format=file_format,
            initial_errors=parse_errors
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset processing failed: {str(e)}")

@router.post("/validate-payload", response_model=DatasetValidationResult)
def validate_payload(payload: ValidatePayloadRequest):
    """
    Directly validates a list of merchant transaction records passed as JSON,
    useful for interactive dashboard testing and quick previews.
    """
    try:
        return validate_merchant_dataset(
            records=payload.records,
            filename=payload.filename or "payload.json",
            file_format="json"
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.get("/sessions/{session_id}")
def get_analysis_session(session_id: str):
    """Retrieves metadata and record summary for an active analysis session."""
    session = get_session_data(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Analysis session '{session_id}' not found or expired.")
    return {
        "session_id": session["session_id"],
        "filename": session["filename"],
        "file_format": session["file_format"],
        "record_count": session["record_count"],
        "uploaded_at": session["uploaded_at"]
    }
