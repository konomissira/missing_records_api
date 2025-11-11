import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Use SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_batch():
    """Sample batch data for testing"""
    return {
        "batch_name": "test_batch_orders",
        "record_type": "order",
        "description": "Test batch for order processing"
    }


@pytest.fixture
def sample_expected_records():
    """Sample expected records for testing"""
    return {
        "records": [
            {"record_id": 1001, "status": "expected", "record_metadata": "Order 1001"},
            {"record_id": 1002, "status": "expected", "record_metadata": "Order 1002"},
            {"record_id": 1003, "status": "expected", "record_metadata": "Order 1003"},
            {"record_id": 1004, "status": "expected", "record_metadata": "Order 1004"},
            {"record_id": 1005, "status": "expected", "record_metadata": "Order 1005"}
        ]
    }


@pytest.fixture
def sample_processed_records():
    """Sample processed records for testing"""
    return {
        "records": [
            {"record_id": 1001, "status": "processed", "record_metadata": "Order 1001 shipped"},
            {"record_id": 1003, "status": "processed", "record_metadata": "Order 1003 shipped"},
            {"record_id": 1005, "status": "processed", "record_metadata": "Order 1005 shipped"}
        ]
    }