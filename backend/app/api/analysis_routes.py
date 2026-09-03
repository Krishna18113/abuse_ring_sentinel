from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any

from app.analysis.schemas import (
    DatasetValidationResult,
    ValidatePayloadRequest,
    SampleDatasetItem,
    SessionAnalysisReport,
    SessionInvestigationResponse,
)
from app.analysis.validator import (
    parse_file_content,
    validate_merchant_dataset,
    get_session_data,
)
from app.analysis.samples import get_sample_datasets
from app.analysis.engine import analyze_session_graph, get_session_customer_investigation

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
        "uploaded_at": session["uploaded_at"],
        "validation_result": session.get("validation_result")
    }

@router.get("/sessions/{session_id}/analyze", response_model=SessionAnalysisReport)
@router.post("/sessions/{session_id}/analyze", response_model=SessionAnalysisReport)
def analyze_session(session_id: str):
    """
    Executes graph construction, clustering, and inductive risk scoring
    on the validated merchant dataset in an isolated session workspace.
    """
    try:
        return analyze_session_graph(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph analysis failed: {str(e)}")

@router.get("/sessions/{session_id}/investigate/{customer_id}", response_model=SessionInvestigationResponse)
def investigate_session_customer(session_id: str, customer_id: str):
    """
    Returns an interactive evidence graph and explanation for a customer 
    within the uploaded merchant dataset session.
    """
    try:
        return get_session_customer_investigation(session_id, customer_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Customer investigation failed: {str(e)}")

@router.get("/sessions/{session_id}/customers/{customer_id}")
def get_session_customer_dossier(session_id: str, customer_id: str):
    """
    Returns a complete customer risk dossier matching /api/risk/customers/{customer_id}
    for rendering the complete Investigation page for an uploaded batch customer.
    """
    try:
        from app.analysis.engine import get_session_customer_full_dossier
        return get_session_customer_full_dossier(session_id, customer_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dossier retrieval failed: {str(e)}")

@router.get("/sessions/{session_id}/customers/{customer_id}/graph")
def get_session_customer_graph(session_id: str, customer_id: str):
    """
    Returns the NetworkGraph payload for an uploaded batch customer.
    """
    try:
        from app.analysis.engine import get_session_customer_graph_response
        return get_session_customer_graph_response(session_id, customer_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph retrieval failed: {str(e)}")

@router.get("/sessions/{session_id}/customers/{customer_id}/explanation")
def get_session_customer_explanation(session_id: str, customer_id: str):
    """
    Returns the AIExplanationCard payload for an uploaded batch customer.
    """
    try:
        from app.analysis.engine import get_session_customer_explanation_response
        return get_session_customer_explanation_response(session_id, customer_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation retrieval failed: {str(e)}")


