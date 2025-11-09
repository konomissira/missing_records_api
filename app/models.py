from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database import Base


class RecordStatus(str, enum.Enum):
    """Enum for record processing status"""
    EXPECTED = "expected"
    PROCESSED = "processed"


class RecordType(str, enum.Enum):
    """Enum for different types of records being tracked"""
    ORDER = "order"
    TRANSACTION = "transaction"
    FILE = "file"
    SHIPMENT = "shipment"
    PAYMENT = "payment"


class Batch(Base):
    """Batch model representing a group of records to track"""
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_name = Column(String, nullable=False, unique=True, index=True)
    record_type = Column(Enum(RecordType), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to records
    records = relationship("Record", back_populates="batch", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Batch(id={self.id}, name={self.batch_name}, type={self.record_type})>"


class Record(Base):
    """Record model representing individual records being tracked through a pipeline"""
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False, index=True)
    status = Column(Enum(RecordStatus), nullable=False, default=RecordStatus.EXPECTED)
    metadata = Column(Text, nullable=True)  # Optional JSON-like metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to batch
    batch = relationship("Batch", back_populates="records")

    def __repr__(self):
        return f"<Record(id={self.id}, record_id={self.record_id}, status={self.status})>"