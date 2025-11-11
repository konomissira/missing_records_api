# Missing Records Detection API

A production-ready REST API for detecting missing records in data pipelines using Python set operations.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-20%20passed-success.svg)](tests/)

## 📋 Overview

This project demonstrates efficient missing data detection for tracking records through processing pipelines (orders, transactions, files, etc.) and identifying gaps using **Python set difference operations**. Built as a real-world example of how data structures solve practical data engineering problems.

### The Problem

**Real-World Scenario:**

-   You expect **5,000 orders** to ship today
-   Only **3,753** made it to the shipping system
-   **Where are the missing 1,247 orders?**

Traditional approaches:

-   ❌ Manual spreadsheet comparison (hours of work)
-   ❌ Nested loops checking each record (O(n²) - too slow)
-   ❌ SQL queries across systems (complex and fragile)
-   ❌ Discovering the problem too late (angry customers)

### The Solution

Using **set difference operations** to efficiently:

-   ✅ Find missing records in O(n) time
-   ✅ Identify unexpected records (processed but not expected)
-   ✅ Calculate processing rates instantly
-   ✅ Monitor pipeline health in real-time

## 🚀 Features

-   **Batch Tracking**: Create batches to track records through pipelines
-   **Expected vs Processed**: Upload what should process and what actually did
-   **Missing Records Detection**: Find gaps using SET DIFFERENCE operation
-   **Unexpected Records**: Identify records that shouldn't be there
-   **Processing Rate**: Calculate success rates automatically
-   **Pipeline Monitoring**: Real-time status tracking
-   **Auto-generated API Docs**: Interactive Swagger UI and ReDoc
-   **Comprehensive Tests**: 20 pytest unit tests covering all functionality
-   **Sample Data**: Pre-built order tracking scenario for quick demos

## 🛠️ Tech Stack

| Technology                  | Purpose                                 |
| --------------------------- | --------------------------------------- |
| **Python 3.11**             | Programming language                    |
| **FastAPI**                 | Modern, high-performance web framework  |
| **PostgreSQL 15**           | Relational database for record tracking |
| **SQLAlchemy**              | ORM for database operations             |
| **Pydantic**                | Data validation and serialisation       |
| **Docker & Docker Compose** | Containerisation and orchestration      |
| **pytest**                  | Testing framework                       |
| **Uvicorn**                 | ASGI web server                         |

## 📦 Installation

### Prerequisites

-   [Docker Desktop](https://www.docker.com/products/docker-desktop) installed
-   [Git](https://git-scm.com/) installed
-   Ports 8000 and 5432 available

### Setup

1. **Clone the repository**

    ```bash
    git clone https://github.com/konomissira/missing_records_api.git
    cd missing_records_api
    ```

2. **Create environment file**

    ```bash
    cp .env.example .env
    ```

3. **Build and start containers**

    ```bash
    docker compose up --build
    ```

4. **Load sample data** (optional)

    ```bash
    docker compose exec app python data/seed_data.py
    ```

5. **Access the API**
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
    - API Root: http://localhost:8000

## 📖 Usage

### Quick Start with Sample Data

```bash
# Start the application
docker compose up -d

# Load sample order tracking data
docker compose exec app python data/seed_data.py

# Access API documentation
open http://localhost:8000/docs
```

**Sample scenario:** 10 orders expected, 7 processed, 3 missing (70% processing rate)

### API Workflow

#### 1. Create a Batch

**POST** `/api/v1/batches`

```bash
curl -X POST "http://localhost:8000/api/v1/batches" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_name": "daily_orders_2025_11_11",
    "record_type": "order",
    "description": "Daily order processing for November 11"
  }'
```

**Response:**

```json
{
    "id": 1,
    "batch_name": "daily_orders_2025_11_11",
    "record_type": "order",
    "description": "Daily order processing for November 11",
    "created_at": "2025-11-11T08:00:00Z"
}
```

#### 2. Upload Expected Records

**POST** `/api/v1/records/bulk`

```bash
curl -X POST "http://localhost:8000/api/v1/records/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": 1,
    "records": [
      {"record_id": 10001, "status": "expected", "record_metadata": "Order 10001"},
      {"record_id": 10002, "status": "expected", "record_metadata": "Order 10002"},
      {"record_id": 10003, "status": "expected", "record_metadata": "Order 10003"},
      {"record_id": 10004, "status": "expected", "record_metadata": "Order 10004"},
      {"record_id": 10005, "status": "expected", "record_metadata": "Order 10005"}
    ]
  }'
```

#### 3. Upload Processed Records

**POST** `/api/v1/records/bulk`

```bash
curl -X POST "http://localhost:8000/api/v1/records/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": 1,
    "records": [
      {"record_id": 10001, "status": "processed", "record_metadata": "Shipped"},
      {"record_id": 10003, "status": "processed", "record_metadata": "Shipped"},
      {"record_id": 10005, "status": "processed", "record_metadata": "Shipped"}
    ]
  }'
```

#### 4. Detect Missing Records (SET DIFFERENCE)

**GET** `/api/v1/analysis/missing/1`

```bash
curl http://localhost:8000/api/v1/analysis/missing/1
```

**Response:**

```json
{
    "batch_id": 1,
    "batch_name": "daily_orders_2025_11_11",
    "total_expected": 5,
    "total_processed": 3,
    "missing_count": 2,
    "missing_records": [10002, 10004],
    "processing_rate": 60.0,
    "unexpected_count": 0,
    "unexpected_records": []
}
```

**Interpretation:**

-   Expected 5 orders to process
-   Only 3 orders actually processed
-   **Missing:** Orders 10002 and 10004
-   Processing rate: 60%

#### 5. Get Processing Status

**GET** `/api/v1/analysis/status/1`

```bash
curl http://localhost:8000/api/v1/analysis/status/1
```

Shows all expected and processed record IDs side by side for easy comparison.

#### 6. Get Batch Statistics

**GET** `/api/v1/analysis/statistics/1`

```bash
curl http://localhost:8000/api/v1/analysis/statistics/1
```

Provides overall statistics and processing rate for the batch.

## 🧮 Set Operations Explained

This project demonstrates the power of set difference operations:

### Finding Missing Records

```python
# Expected to process
expected = {10001, 10002, 10003, 10004, 10005}

# Actually processed
processed = {10001, 10003, 10005}

# SET DIFFERENCE: Find missing records
missing = expected - processed  # {10002, 10004}
```

**Result:** 2 missing records identified instantly

### Finding Unexpected Records

```python
# Reverse difference: processed but not expected
unexpected = processed - expected
```

**Result:** Identifies records that shouldn't have been processed

### Calculate Success Rate

```python
# SET INTERSECTION: Successfully processed
successful = expected & processed  # {10001, 10003, 10005}

# Calculate rate
processing_rate = len(successful) / len(expected) * 100  # 60%
```

## 🧪 Testing

Run the test suite with pytest:

```bash
# Run all tests
docker compose exec app pytest

# Run with verbose output
docker compose exec app pytest -v

# Run specific test class
docker compose exec app pytest tests/test_missing_records.py::TestMissingRecordsDetection -v

# Run locally (without Docker)
pytest -v
```

**Test Coverage:**

-   ✅ Health check endpoints
-   ✅ Batch creation and management
-   ✅ Record upload (single and bulk)
-   ✅ Missing records detection (SET DIFFERENCE)
-   ✅ Processing status tracking
-   ✅ Batch statistics calculation
-   ✅ Edge cases (no data, all processed, none processed, unexpected records)
-   ✅ Data cleanup operations

**Result:** 20 tests passing ✅

## 📁 Project Structure

```
missing-records-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database connection and session management
│   ├── models.py            # SQLAlchemy models (Batch, Record)
│   ├── schemas.py           # Pydantic schemas for validation
│   ├── services.py          # Business logic (set difference operations)
│   └── api/
│       ├── __init__.py
│       └── endpoints.py     # API route definitions
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures and configuration
│   └── test_missing_records.py  # Unit tests
├── data/
│   ├── README.md            # Sample data documentation
│   ├── sample_orders.json   # Sample order tracking data
│   ├── sample_orders.csv    # CSV format sample data
│   └── seed_data.py         # Script to load sample data
├── .env.example             # Environment variables template
├── .gitignore
├── docker-compose.yml       # Docker orchestration
├── Dockerfile               # Container definition
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Development

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_USER=missing_records_user
export POSTGRES_PASSWORD=missing_records_password
export POSTGRES_DB=missing_records_db

# Run the application
uvicorn app.main:app --reload --port 8000
```

### Stopping the Application

```bash
# Stop containers
docker compose down

# Stop and remove volumes (clears database)
docker compose down -v
```

## 📊 Performance

Set difference operations provide excellent performance characteristics:

| Operation          | Time Complexity | Space Complexity |
| ------------------ | --------------- | ---------------- |
| Difference (`-`)   | O(n)            | O(n)             |
| Intersection (`&`) | O(min(n, m))    | O(min(n, m))     |
| Union (`\|`)       | O(n + m)        | O(n + m)         |

Where n and m are the sizes of the input sets.

**Example:** Finding missing records in a batch of 1 million records takes ~0.1 seconds using set difference, compared to minutes or hours with nested loops.

## 🎯 Use Cases

This API is designed for various data pipeline scenarios:

-   📦 **Order fulfillment** - Track which orders didn't ship
-   💳 **Payment processing** - Identify failed transactions
-   📄 **File processing** - Find files that weren't processed
-   🚚 **Shipment tracking** - Detect stuck shipments
-   📊 **ETL pipelines** - Validate data loads
-   🔄 **Data synchronisation** - Verify sync completion
-   📨 **Email campaigns** - Track undelivered messages
-   🎫 **Ticket processing** - Monitor support queues

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add some TheFeatureYouAdd'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

Built as part of a data engineering portfolio project - Project 2 of 4.

Demonstrating:

-   Clean architecture and design patterns
-   RESTful API development with FastAPI
-   Database modeling with SQLAlchemy
-   Docker containerization
-   Test-driven development with pytest
-   Professional Git workflow with feature branches
-   Comprehensive documentation
-   Practical application of set operations

## 🔗 Related Resources

-   [FastAPI Documentation](https://fastapi.tiangolo.com/)
-   [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
-   [Docker Documentation](https://docs.docker.com/)
-   [Python Set Operations](https://docs.python.org/3/tutorial/datastructures.html#sets)

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with ❤️ using Python, FastAPI, and PostgreSQL**
