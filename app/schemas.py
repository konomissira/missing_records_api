from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from app.models import RecordStatus, RecordType


# Batch schemas
class BatchCreate(BaseModel):
    """Schema for creating a new batch"""
    batch_name: str = Field(..., min_length=1, max_length=255, description="Unique batch name")
    record_type: RecordType = Field(..., description="Type of records in this batch")
    description: Optional[str] = Field(None, description="Optional batch description")


class BatchResponse(BaseModel):
    """Schema for batch response"""
    id: int
    batch_name: str
    record_type: RecordType
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Record schemas
class RecordCreate(BaseModel):
    """Schema for creating a single record"""
    record_id: int = Field(..., description="ID of the record to track")
    status: RecordStatus = Field(..., description="Record status (expected or processed)")
    record_metadata: Optional[str] = Field(None, description="Optional metadata")


class RecordBulkUpload(BaseModel):
    """Schema for bulk uploading records"""
    batch_id: int = Field(..., description="Batch ID to add records to")
    records: List[RecordCreate]


class RecordResponse(BaseModel):
    """Schema for record response"""
    id: int
    record_id: int
    batch_id: int
    status: RecordStatus
    #metadata: Optional[str]
    record_metadata: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Analysis schemas
class MissingRecordsResult(BaseModel):
    """Schema for missing records analysis using SET DIFFERENCE"""
    batch_id: int
    batch_name: str
    total_expected: int
    total_processed: int
    missing_count: int
    missing_records: List[int]
    processing_rate: float
    unexpected_count: int
    unexpected_records: List[int]


class ProcessingStatusResult(BaseModel):
    """Schema for overall processing status"""
    batch_id: int
    batch_name: str
    record_type: RecordType
    expected_records: List[int]
    processed_records: List[int]
    expected_count: int
    processed_count: int


class BatchStatistics(BaseModel):
    """Schema for batch statistics"""
    batch_id: int
    batch_name: str
    total_records: int
    expected_count: int
    processed_count: int
    missing_count: int
    processing_rate: float


class MessageResponse(BaseModel):
    """Schema for simple message responses"""
    message: str
    details: Optional[dict] = None