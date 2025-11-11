import pytest
from fastapi import status


class TestHealthEndpoints:
    """Test basic health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "healthy"


class TestBatchManagement:
    """Test batch creation and management"""
    
    def test_create_batch(self, client, sample_batch):
        """Test creating a new batch"""
        response = client.post("/api/v1/batches", json=sample_batch)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["batch_name"] == sample_batch["batch_name"]
        assert data["record_type"] == sample_batch["record_type"]
        assert "id" in data
    
    def test_create_duplicate_batch(self, client, sample_batch):
        """Test creating a batch with duplicate name fails"""
        # Create first batch
        client.post("/api/v1/batches", json=sample_batch)
        
        # Try to create duplicate
        response = client.post("/api/v1/batches", json=sample_batch)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_all_batches_empty(self, client):
        """Test getting batches when none exist"""
        response = client.get("/api/v1/batches")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_get_all_batches(self, client, sample_batch):
        """Test getting all batches"""
        # Create a batch
        client.post("/api/v1/batches", json=sample_batch)
        
        # Get all batches
        response = client.get("/api/v1/batches")
        assert response.status_code == status.HTTP_200_OK
        batches = response.json()
        assert len(batches) == 1
        assert batches[0]["batch_name"] == sample_batch["batch_name"]
    
    def test_get_batch_by_id(self, client, sample_batch):
        """Test getting a specific batch by ID"""
        # Create batch
        create_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = create_response.json()["id"]
        
        # Get batch by ID
        response = client.get(f"/api/v1/batches/{batch_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == batch_id
    
    def test_get_nonexistent_batch(self, client):
        """Test getting a batch that doesn't exist"""
        response = client.get("/api/v1/batches/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_batch(self, client, sample_batch):
        """Test deleting a batch"""
        # Create batch
        create_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = create_response.json()["id"]
        
        # Delete batch
        response = client.delete(f"/api/v1/batches/{batch_id}")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify it's gone
        response = client.get(f"/api/v1/batches/{batch_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRecordManagement:
    """Test record creation and management"""
    
    def test_create_single_record(self, client, sample_batch):
        """Test creating a single record"""
        # Create batch first
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        # Create record
        record_data = {
            "record_id": 2001,
            "status": "expected",
            "record_metadata": "Test order"
        }
        response = client.post(f"/api/v1/records?batch_id={batch_id}", json=record_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["record_id"] == 2001
        assert data["status"] == "expected"
    
    def test_bulk_upload_records(self, client, sample_batch, sample_expected_records):
        """Test bulk uploading records"""
        # Create batch
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        # Bulk upload
        bulk_data = {
            "batch_id": batch_id,
            "records": sample_expected_records["records"]
        }
        response = client.post("/api/v1/records/bulk", json=bulk_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "Successfully uploaded 5 records" in data["message"]
    
    def test_get_records_by_batch(self, client, sample_batch, sample_expected_records):
        """Test getting all records for a batch"""
        # Create batch and records
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        bulk_data = {
            "batch_id": batch_id,
            "records": sample_expected_records["records"]
        }
        client.post("/api/v1/records/bulk", json=bulk_data)
        
        # Get records
        response = client.get(f"/api/v1/records/batch/{batch_id}")
        assert response.status_code == status.HTTP_200_OK
        records = response.json()
        assert len(records) == 5
    
    def test_get_records_by_status(self, client, sample_batch, sample_expected_records, sample_processed_records):
        """Test getting records by status"""
        # Create batch
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        # Upload expected records
        bulk_expected = {"batch_id": batch_id, "records": sample_expected_records["records"]}
        client.post("/api/v1/records/bulk", json=bulk_expected)
        
        # Upload processed records
        bulk_processed = {"batch_id": batch_id, "records": sample_processed_records["records"]}
        client.post("/api/v1/records/bulk", json=bulk_processed)
        
        # Get expected records
        response = client.get(f"/api/v1/records/batch/{batch_id}/status/expected")
        assert response.status_code == status.HTTP_200_OK
        expected = response.json()
        assert len(expected) == 5
        
        # Get processed records
        response = client.get(f"/api/v1/records/batch/{batch_id}/status/processed")
        assert response.status_code == status.HTTP_200_OK
        processed = response.json()
        assert len(processed) == 3


class TestMissingRecordsDetection:
    """Test missing records detection using SET DIFFERENCE"""
    
    def test_missing_records_with_no_data(self, client, sample_batch):
        """Test missing records analysis when no records exist"""
        # Create batch with no records
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        # Analyse missing records
        response = client.get(f"/api/v1/analysis/missing/{batch_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total_expected"] == 0
        assert data["total_processed"] == 0
        assert data["missing_count"] == 0
        assert data["missing_records"] == []
        assert data["processing_rate"] == 0.0
    
    def test_missing_records_detection(self, client, sample_batch, sample_expected_records, sample_processed_records):
        """Test missing records detection using SET DIFFERENCE"""
        # Create batch
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        # Upload expected records (5 records)
        bulk_expected = {"batch_id": batch_id, "records": sample_expected_records["records"]}
        client.post("/api/v1/records/bulk", json=bulk_expected)
        
        # Upload processed records (3 records)
        bulk_processed = {"batch_id": batch_id, "records": sample_processed_records["records"]}
        client.post("/api/v1/records/bulk", json=bulk_processed)
        
        # Analyse missing records
        response = client.get(f"/api/v1/analysis/missing/{batch_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify results
        assert data["total_expected"] == 5
        assert data["total_processed"] == 3
        assert data["missing_count"] == 2
        assert data["missing_records"] == [1002, 1004]  # SET DIFFERENCE in action!
        assert data["processing_rate"] == 60.0  # 3 out of 5 = 60%
        assert data["unexpected_count"] == 0
        assert data["unexpected_records"] == []
    
    def test_all_records_processed(self, client, sample_batch):
        """Test when all expected records are processed"""
        # Create batch
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        # Upload expected and processed (same records)
        records = [
            {"record_id": 3001, "status": "expected", "record_metadata": "Order 3001"},
            {"record_id": 3002, "status": "expected", "record_metadata": "Order 3002"}
        ]
        bulk_expected = {"batch_id": batch_id, "records": records}
        client.post("/api/v1/records/bulk", json=bulk_expected)
        
        processed = [
            {"record_id": 3001, "status": "processed", "record_metadata": "Order 3001"},
            {"record_id": 3002, "status": "processed", "record_metadata": "Order 3002"}
        ]
        bulk_processed = {"batch_id": batch_id, "records": processed}
        client.post("/api/v1/records/bulk", json=bulk_processed)
        
        # Analyse
        response = client.get(f"/api/v1/analysis/missing/{batch_id}")
        data = response.json()
        
        assert data["missing_count"] == 0
        assert data["missing_records"] == []
        assert data["processing_rate"] == 100.0
    
    def test_no_records_processed(self, client, sample_batch):
        """Test when no expected records were processed"""
        # Create batch
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        # Upload only expected records
        records = [
            {"record_id": 4001, "status": "expected", "record_metadata": "Order 4001"},
            {"record_id": 4002, "status": "expected", "record_metadata": "Order 4002"}
        ]
        bulk_expected = {"batch_id": batch_id, "records": records}
        client.post("/api/v1/records/bulk", json=bulk_expected)
        
        # Analyse
        response = client.get(f"/api/v1/analysis/missing/{batch_id}")
        data = response.json()
        
        assert data["total_expected"] == 2
        assert data["total_processed"] == 0
        assert data["missing_count"] == 2
        assert data["missing_records"] == [4001, 4002]
        assert data["processing_rate"] == 0.0
    
    def test_unexpected_records(self, client, sample_batch):
        """Test when processed records include unexpected ones"""
        # Create batch
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        # Upload expected records
        expected = [
            {"record_id": 5001, "status": "expected", "record_metadata": "Order 5001"}
        ]
        bulk_expected = {"batch_id": batch_id, "records": expected}
        client.post("/api/v1/records/bulk", json=bulk_expected)
        
        # Upload processed records (includes unexpected)
        processed = [
            {"record_id": 5001, "status": "processed", "record_metadata": "Order 5001"},
            {"record_id": 9999, "status": "processed", "record_metadata": "Unexpected order"}
        ]
        bulk_processed = {"batch_id": batch_id, "records": processed}
        client.post("/api/v1/records/bulk", json=bulk_processed)
        
        # Analyse
        response = client.get(f"/api/v1/analysis/missing/{batch_id}")
        data = response.json()
        
        assert data["unexpected_count"] == 1
        assert data["unexpected_records"] == [9999]  # Processed but not expected!


class TestProcessingStatus:
    """Test processing status endpoints"""
    
    def test_get_processing_status(self, client, sample_batch, sample_expected_records, sample_processed_records):
        """Test getting processing status for a batch"""
        # Create batch
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        # Upload records
        bulk_expected = {"batch_id": batch_id, "records": sample_expected_records["records"]}
        client.post("/api/v1/records/bulk", json=bulk_expected)
        
        bulk_processed = {"batch_id": batch_id, "records": sample_processed_records["records"]}
        client.post("/api/v1/records/bulk", json=bulk_processed)
        
        # Get status
        response = client.get(f"/api/v1/analysis/status/{batch_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["batch_id"] == batch_id
        assert data["expected_count"] == 5
        assert data["processed_count"] == 3
        assert data["expected_records"] == [1001, 1002, 1003, 1004, 1005]
        assert data["processed_records"] == [1001, 1003, 1005]
    
    def test_get_batch_statistics(self, client, sample_batch, sample_expected_records, sample_processed_records):
        """Test getting batch statistics"""
        # Create batch
        batch_response = client.post("/api/v1/batches", json=sample_batch)
        batch_id = batch_response.json()["id"]
        
        # Upload records
        bulk_expected = {"batch_id": batch_id, "records": sample_expected_records["records"]}
        client.post("/api/v1/records/bulk", json=bulk_expected)
        
        bulk_processed = {"batch_id": batch_id, "records": sample_processed_records["records"]}
        client.post("/api/v1/records/bulk", json=bulk_processed)
        
        # Get statistics
        response = client.get(f"/api/v1/analysis/statistics/{batch_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["batch_id"] == batch_id
        assert data["total_records"] == 8  # 5 expected + 3 processed
        assert data["expected_count"] == 5