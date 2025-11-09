from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Batch, Record, RecordStatus, RecordType
from app.schemas import (
    BatchCreate, RecordCreate, MissingRecordsResult, 
    ProcessingStatusResult, BatchStatistics
)
from typing import List, Optional


class BatchService:
    """Service class for batch operations"""

    @staticmethod
    def create_batch(db: Session, batch_data: BatchCreate) -> Batch:
        """Create a new batch for tracking records"""
        batch = Batch(
            batch_name=batch_data.batch_name,
            record_type=batch_data.record_type,
            description=batch_data.description
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch

    @staticmethod
    def get_batch_by_id(db: Session, batch_id: int) -> Optional[Batch]:
        """Get batch by ID"""
        return db.query(Batch).filter(Batch.id == batch_id).first()

    @staticmethod
    def get_batch_by_name(db: Session, batch_name: str) -> Optional[Batch]:
        """Get batch by name"""
        return db.query(Batch).filter(Batch.batch_name == batch_name).first()

    @staticmethod
    def get_all_batches(db: Session) -> List[Batch]:
        """Get all batches"""
        return db.query(Batch).all()

    @staticmethod
    def delete_batch(db: Session, batch_id: int) -> bool:
        """Delete a batch and all its records"""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch:
            db.delete(batch)
            db.commit()
            return True
        return False


class RecordService:
    """Service class for record tracking and missing records detection"""

    @staticmethod
    def create_record(db: Session, batch_id: int, record_data: RecordCreate) -> Record:
        """Create a single record"""
        record = Record(
            record_id=record_data.record_id,
            batch_id=batch_id,
            status=record_data.status,
            record_metadata=record_data.record_metadata
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def bulk_create_records(db: Session, batch_id: int, records_data: List[RecordCreate]) -> List[Record]:
        """Bulk create records"""
        records = [
            Record(
                record_id=record_data.record_id,
                batch_id=batch_id,
                status=record_data.status,
                record_metadata=record_data.record_metadata

            )
            for record_data in records_data
        ]
        db.add_all(records)
        db.commit()
        return records

    @staticmethod
    def get_records_by_batch(db: Session, batch_id: int) -> List[Record]:
        """Get all records for a batch"""
        return db.query(Record).filter(Record.batch_id == batch_id).all()

    @staticmethod
    def get_records_by_status(db: Session, batch_id: int, status: RecordStatus) -> List[Record]:
        """Get records by status for a specific batch"""
        return db.query(Record).filter(
            Record.batch_id == batch_id,
            Record.status == status
        ).all()

    @staticmethod
    def find_missing_records(db: Session, batch_id: int) -> MissingRecordsResult:
        """
        Find missing records using SET DIFFERENCE operation
        
        Returns records that are expected but not processed,
        and records that were processed but not expected.
        """
        # Get the batch
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise ValueError(f"Batch with id {batch_id} not found")

        # Get expected records
        expected_records = db.query(Record.record_id).filter(
            Record.batch_id == batch_id,
            Record.status == RecordStatus.EXPECTED
        ).all()
        expected_ids = set([r.record_id for r in expected_records])

        # Get processed records
        processed_records = db.query(Record.record_id).filter(
            Record.batch_id == batch_id,
            Record.status == RecordStatus.PROCESSED
        ).all()
        processed_ids = set([r.record_id for r in processed_records])

        # SET DIFFERENCE OPERATIONS
        # Missing: Expected but not processed
        missing = expected_ids - processed_ids
        
        # Unexpected: Processed but not expected
        unexpected = processed_ids - expected_ids

        # Calculate processing rate
        total_expected = len(expected_ids)
        total_processed = len(processed_ids)
        
        if total_expected > 0:
            # Processing rate based on expected records that were successfully processed
            successfully_processed = len(expected_ids & processed_ids)
            processing_rate = (successfully_processed / total_expected) * 100
        else:
            processing_rate = 0.0

        return MissingRecordsResult(
            batch_id=batch_id,
            batch_name=batch.batch_name,
            total_expected=total_expected,
            total_processed=total_processed,
            missing_count=len(missing),
            missing_records=sorted(list(missing)),
            processing_rate=round(processing_rate, 2),
            unexpected_count=len(unexpected),
            unexpected_records=sorted(list(unexpected))
        )

    @staticmethod
    def get_processing_status(db: Session, batch_id: int) -> ProcessingStatusResult:
        """
        Get processing status for a batch
        Shows all expected and processed record IDs
        """
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise ValueError(f"Batch with id {batch_id} not found")

        # Get expected records
        expected_records = db.query(Record.record_id).filter(
            Record.batch_id == batch_id,
            Record.status == RecordStatus.EXPECTED
        ).all()
        expected_ids = [r.record_id for r in expected_records]

        # Get processed records
        processed_records = db.query(Record.record_id).filter(
            Record.batch_id == batch_id,
            Record.status == RecordStatus.PROCESSED
        ).all()
        processed_ids = [r.record_id for r in processed_records]

        return ProcessingStatusResult(
            batch_id=batch_id,
            batch_name=batch.batch_name,
            record_type=batch.record_type,
            expected_records=sorted(expected_ids),
            processed_records=sorted(processed_ids),
            expected_count=len(expected_ids),
            processed_count=len(processed_ids)
        )

    @staticmethod
    def get_batch_statistics(db: Session, batch_id: int) -> BatchStatistics:
        """Get statistics for a batch"""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise ValueError(f"Batch with id {batch_id} not found")

        # Count records by status
        total_records = db.query(func.count(Record.id)).filter(
            Record.batch_id == batch_id
        ).scalar()

        expected_count = db.query(func.count(Record.id)).filter(
            Record.batch_id == batch_id,
            Record.status == RecordStatus.EXPECTED
        ).scalar()

        processed_count = db.query(func.count(Record.id)).filter(
            Record.batch_id == batch_id,
            Record.status == RecordStatus.PROCESSED
        ).scalar()

        # Get unique expected and processed IDs
        expected_records = db.query(Record.record_id).filter(
            Record.batch_id == batch_id,
            Record.status == RecordStatus.EXPECTED
        ).all()
        expected_ids = set([r.record_id for r in expected_records])

        processed_records = db.query(Record.record_id).filter(
            Record.batch_id == batch_id,
            Record.status == RecordStatus.PROCESSED
        ).all()
        processed_ids = set([r.record_id for r in processed_records])

        # Calculate missing
        missing_count = len(expected_ids - processed_ids)

        # Calculate processing rate
        if len(expected_ids) > 0:
            successfully_processed = len(expected_ids & processed_ids)
            processing_rate = (successfully_processed / len(expected_ids)) * 100
        else:
            processing_rate = 0.0

        return BatchStatistics(
            batch_id=batch_id,
            batch_name=batch.batch_name,
            total_records=total_records,
            expected_count=expected_count,
            processed_count=processed_count,
            missing_count=missing_count,
            processing_rate=round(processing_rate, 2)
        )

    @staticmethod
    def clear_all_records(db: Session, batch_id: int) -> int:
        """Delete all records for a batch"""
        count = db.query(Record).filter(Record.batch_id == batch_id).delete()
        db.commit()
        return count