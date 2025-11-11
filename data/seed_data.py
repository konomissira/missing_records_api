#!/usr/bin/env python3
"""
Script to seed the database with sample order tracking data
Usage: python data/seed_data.py
"""
import json
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models import Batch, Record, RecordType, RecordStatus


def clear_existing_data(db):
    """Clear all existing data"""
    record_count = db.query(Record).delete()
    batch_count = db.query(Batch).delete()
    db.commit()
    print(f"Cleared {batch_count} existing batches and {record_count} existing records")


def load_sample_data(db, clear_first=True):
    """Load sample order tracking data from JSON file"""
    if clear_first:
        clear_existing_data(db)
    
    # Read sample data file
    json_file = os.path.join(os.path.dirname(__file__), 'sample_orders.json')
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Create batch
    batch = Batch(
        batch_name=data['batch']['batch_name'],
        record_type=RecordType(data['batch']['record_type']),
        description=data['batch']['description']
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    
    print(f"Created batch: {batch.batch_name} (ID: {batch.id})")
    
    # Create expected records
    expected_records = []
    for record_data in data['expected_records']:
        record = Record(
            record_id=record_data['record_id'],
            batch_id=batch.id,
            status=RecordStatus(record_data['status']),
            record_metadata=record_data['record_metadata']
        )
        expected_records.append(record)
    
    db.add_all(expected_records)
    db.commit()
    
    print(f"Loaded {len(expected_records)} expected records")
    
    # Create processed records
    processed_records = []
    for record_data in data['processed_records']:
        record = Record(
            record_id=record_data['record_id'],
            batch_id=batch.id,
            status=RecordStatus(record_data['status']),
            record_metadata=record_data['record_metadata']
        )
        processed_records.append(record)
    
    db.add_all(processed_records)
    db.commit()
    
    print(f"Loaded {len(processed_records)} processed records")
    
    # Calculate and display summary statistics
    print("\n--- Summary ---")
    print(f"Batch: {batch.batch_name}")
    print(f"Expected orders: {len(expected_records)}")
    print(f"Processed orders: {len(processed_records)}")
    
    # Calculate missing using set operations
    expected_ids = set(r.record_id for r in expected_records)
    processed_ids = set(r.record_id for r in processed_records)
    
    missing_ids = expected_ids - processed_ids  # SET DIFFERENCE
    successfully_processed = expected_ids & processed_ids  # SET INTERSECTION
    
    print(f"\nSuccessfully processed: {len(successfully_processed)} orders")
    print(f"Missing (not processed): {len(missing_ids)} orders")
    print(f"Missing order IDs: {sorted(list(missing_ids))}")
    
    if len(expected_ids) > 0:
        processing_rate = (len(successfully_processed) / len(expected_ids)) * 100
        print(f"Processing rate: {processing_rate:.1f}%")
    
    return batch.id


def main():
    """Main function"""
    print("=" * 60)
    print("Missing Records Detection API - Data Seeding")
    print("=" * 60)
    print()
    
    # Create database session
    db = SessionLocal()
    
    try:
        batch_id = load_sample_data(db, clear_first=True)
        print("\n✅ Database seeded successfully!")
        print(f"\nBatch ID: {batch_id}")
        print("\nYou can now:")
        print("1. Visit http://localhost:8001/docs to test the API")
        print(f"2. Try GET /api/v1/analysis/missing/{batch_id}")
        print(f"3. Try GET /api/v1/analysis/status/{batch_id}")
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()