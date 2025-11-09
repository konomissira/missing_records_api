from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import (
    BatchCreate, BatchResponse, RecordCreate, RecordResponse,
    RecordBulkUpload, MissingRecordsResult, ProcessingStatusResult,
    BatchStatistics, MessageResponse
)
from app.models import RecordStatus
from app.services import BatchService, RecordService

router = APIRouter(prefix="/api/v1", tags=["records"])


# Batch endpoints
@router.post("/batches", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(
    batch: BatchCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new batch for tracking records through a pipeline
    """
    # Check if batch name already exists
    existing = BatchService.get_batch_by_name(db, batch.batch_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch with name '{batch.batch_name}' already exists"
        )
    
    try:
        new_batch = BatchService.create_batch(db, batch)
        return new_batch
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create batch: {str(e)}"
        )


@router.get("/batches", response_model=List[BatchResponse])
def get_all_batches(db: Session = Depends(get_db)):
    """
    Get all batches
    """
    batches = BatchService.get_all_batches(db)
    return batches


@router.get("/batches/{batch_id}", response_model=BatchResponse)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific batch by ID
    """
    batch = BatchService.get_batch_by_id(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {batch_id} not found"
        )
    return batch


@router.delete("/batches/{batch_id}", response_model=MessageResponse)
def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a batch and all its records
    """
    deleted = BatchService.delete_batch(db, batch_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {batch_id} not found"
        )
    return MessageResponse(
        message=f"Successfully deleted batch {batch_id}",
        details={"batch_id": batch_id}
    )


# Record endpoints
@router.post("/records", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    batch_id: int,
    record: RecordCreate,
    db: Session = Depends(get_db)
):
    """
    Create a single record for a batch
    """
    # Verify batch exists
    batch = BatchService.get_batch_by_id(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {batch_id} not found"
        )
    
    try:
        new_record = RecordService.create_record(db, batch_id, record)
        return new_record
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create record: {str(e)}"
        )


@router.post("/records/bulk", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def bulk_upload_records(
    bulk_data: RecordBulkUpload,
    db: Session = Depends(get_db)
):
    """
    Bulk upload records for a batch
    """
    # Verify batch exists
    batch = BatchService.get_batch_by_id(db, bulk_data.batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {bulk_data.batch_id} not found"
        )
    
    try:
        records = RecordService.bulk_create_records(db, bulk_data.batch_id, bulk_data.records)
        return MessageResponse(
            message=f"Successfully uploaded {len(records)} records",
            details={"count": len(records), "batch_id": bulk_data.batch_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to bulk upload records: {str(e)}"
        )


@router.get("/records/batch/{batch_id}", response_model=List[RecordResponse])
def get_records_by_batch(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all records for a specific batch
    """
    # Verify batch exists
    batch = BatchService.get_batch_by_id(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {batch_id} not found"
        )
    
    records = RecordService.get_records_by_batch(db, batch_id)
    return records


@router.get("/records/batch/{batch_id}/status/{status}", response_model=List[RecordResponse])
def get_records_by_status(
    batch_id: int,
    status: RecordStatus,
    db: Session = Depends(get_db)
):
    """
    Get records by status (expected or processed) for a specific batch
    """
    # Verify batch exists
    batch = BatchService.get_batch_by_id(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {batch_id} not found"
        )
    
    records = RecordService.get_records_by_status(db, batch_id, status)
    return records


# Missing records detection endpoints (SET DIFFERENCE!)
@router.get("/analysis/missing/{batch_id}", response_model=MissingRecordsResult)
def analyze_missing_records(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    Analyze missing records using SET DIFFERENCE operation
    
    Finds:
    - Records expected but not processed (missing)
    - Records processed but not expected (unexpected)
    - Processing rate
    
    This is the core missing records detection using set operations!
    """
    try:
        result = RecordService.find_missing_records(db, batch_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze missing records: {str(e)}"
        )


@router.get("/analysis/status/{batch_id}", response_model=ProcessingStatusResult)
def get_processing_status(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    Get processing status for a batch
    Shows all expected and processed record IDs
    """
    try:
        result = RecordService.get_processing_status(db, batch_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing status: {str(e)}"
        )


@router.get("/analysis/statistics/{batch_id}", response_model=BatchStatistics)
def get_batch_statistics(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    Get statistics for a batch
    """
    try:
        result = RecordService.get_batch_statistics(db, batch_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch statistics: {str(e)}"
        )


@router.delete("/records/batch/{batch_id}", response_model=MessageResponse)
def clear_batch_records(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete all records for a batch (useful for testing/reset)
    """
    # Verify batch exists
    batch = BatchService.get_batch_by_id(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id {batch_id} not found"
        )
    
    count = RecordService.clear_all_records(db, batch_id)
    return MessageResponse(
        message=f"Successfully deleted all records for batch {batch_id}",
        details={"deleted_count": count, "batch_id": batch_id}
    )