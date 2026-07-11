from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth.auth_service import auth_service
from app.models.user import User
from app.services.credit.credit_service import reserve_credits, complete_credit_deduction, has_sufficient_credits
from app.core.config import CONVERT_CREDITS

from app.schemas.literature_requests import ConversionType
from app.services.literature.artifact_manager import create_job, serialize_artifact, set_job_response, store_artifact
from app.services.literature.cleanup import cleanup_expired_artifacts
from app.services.literature.exporter import dataframe_to_csv_bytes, dataframe_to_nbib_bytes, dataframe_to_ris_bytes
from app.services.literature.normalizer import standardize_dataframe
from app.services.literature.parser import normalize_imported_dataframe, parse_upload, parse_source_database
from app.services.literature.pipeline import preview_records

router = APIRouter(prefix="/api/literature", tags=["convert"])


@router.post("/convert")
async def convert_file(
    file: UploadFile = File(...),
    conversion: ConversionType = Form(...),
    artifact_lifetime_minutes: int = Form(30),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Convert one literature file between RIS, NBIB, and CSV."""
    cleanup_expired_artifacts()

    if not has_sufficient_credits(db, current_user.id, CONVERT_CREDITS):
        raise HTTPException(status_code=402, detail="Payment Required: Insufficient credits.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty upload")

    try:
        source_type, dataframe = parse_upload(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if dataframe.empty:
        raise HTTPException(status_code=400, detail="The uploaded file contains no valid records.")

    if conversion.endswith("_CSV"):
        dataframe = normalize_imported_dataframe(dataframe)
        dataframe = standardize_dataframe(
            dataframe, source_database=parse_source_database(file.filename), source_type=source_type
        )
        export_bytes = dataframe_to_csv_bytes(dataframe)
        export_name = "converted.csv"
        mime_type = "text/csv"
    elif conversion.endswith("_RIS"):
        export_bytes = dataframe_to_ris_bytes(dataframe)
        export_name = "converted.ris"
        mime_type = "application/x-research-info-systems"
    else:
        export_bytes = dataframe_to_nbib_bytes(dataframe)
        export_name = "converted.nbib"
        mime_type = "application/x-nbib"

    job_id = f"job_convert_{file.filename}_{conversion}"

    ledger = reserve_credits(db, current_user.id, CONVERT_CREDITS, feature="convert", job_id=job_id)
    complete_credit_deduction(db, ledger.id)

    create_job(job_id, artifact_lifetime_minutes)
    store_artifact(job_id, export_name, export_bytes)

    preview = preview_records(dataframe)
    response_payload = {
        "jobId": job_id,
        "message": "Conversion successful.",
        "downloadUrl": f"/api/literature/download/{job_id}/{export_name}",
        "recordCount": len(dataframe),
        "preview": preview,
        "exportName": export_name,
        "mimeType": mime_type,
    }
    set_job_response(job_id, response_payload)
    return response_payload
