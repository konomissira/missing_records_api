# Sample Data

This directory contains sample order tracking data for testing and demonstrating the missing records detection API.

## Files

### `sample_orders.json`

JSON format sample data representing a daily order processing batch:

-   **Batch**: "daily_orders_2025_11_01" - Order processing for November 1, 2025
-   **Expected records**: 10 orders that should be processed
-   **Processed records**: 7 orders that were actually processed

### `sample_orders.csv`

Same data in CSV format for alternative loading methods.

### `seed_data.py`

Python script to automatically load sample data into the database.

## Data Overview

The sample data demonstrates a real-world scenario: **order fulfillment tracking**.

### Expected Orders (10 total)

Orders that **should** be processed and shipped today:

-   Order 10001 - Customer A - $150.00
-   Order 10002 - Customer B - $225.50
-   Order 10003 - Customer C - $89.99
-   Order 10004 - Customer D - $320.00 ⚠️ **MISSING**
-   Order 10005 - Customer E - $175.25
-   Order 10006 - Customer F - $450.00 ⚠️ **MISSING**
-   Order 10007 - Customer G - $99.99
-   Order 10008 - Customer H - $275.80
-   Order 10009 - Customer I - $150.00 ⚠️ **MISSING**
-   Order 10010 - Customer J - $399.99

### Processed Orders (7 total)

Orders that **actually** shipped:

-   Order 10001 - Shipped via FedEx ✅
-   Order 10002 - Shipped via UPS ✅
-   Order 10003 - Shipped via USPS ✅
-   Order 10005 - Shipped via FedEx ✅
-   Order 10007 - Shipped via UPS ✅
-   Order 10008 - Shipped via FedEx ✅
-   Order 10010 - Shipped via UPS ✅

### Expected Results

When analysing this data using SET DIFFERENCE operations:

**Missing Records:**

```python
expected = {10001, 10002, 10003, 10004, 10005, 10006, 10007, 10008, 10009, 10010}
processed = {10001, 10002, 10003, 10005, 10007, 10008, 10010}

# SET DIFFERENCE: Find missing records
missing = expected - processed  # {10004, 10006, 10009}
```

**Results:**

-   **Total expected**: 10 orders
-   **Total processed**: 7 orders
-   **Missing**: 3 orders (10004, 10006, 10009)
-   **Processing rate**: 70% (7 out of 10)
-   **Unexpected records**: 0

**Why missing?**

-   Order 10004 ($320.00) - Stuck in inventory
-   Order 10006 ($450.00) - Payment processing issue
-   Order 10009 ($150.00) - Address validation failure

## Usage

### Load Sample Data into Database

**From outside the Docker container:**

```bash
docker-compose exec app python data/seed_data.py
```

**From inside the Docker container:**

```bash
docker-compose exec app bash
python data/seed_data.py
```

**Running locally (without Docker):**

```bash
python data/seed_data.py
```

### Expected Output

```
============================================================
Missing Records Detection API - Data Seeding
============================================================

Cleared 0 existing batches and 0 existing records
Created batch: daily_orders_2025_11_01 (ID: 1)
Loaded 10 expected records
Loaded 7 processed records

--- Summary ---
Batch: daily_orders_2025_11_01
Expected orders: 10
Processed orders: 7

Successfully processed: 7 orders
Missing (not processed): 3 orders
Missing order IDs: [10004, 10006, 10009]
Processing rate: 70.0%

✅ Database seeded successfully!

Batch ID: 1

You can now:
1. Visit http://localhost:8001/docs to test the API
2. Try GET /api/v1/analysis/missing/1
3. Try GET /api/v1/analysis/status/1
```

### Using the API with Sample Data

After seeding, try these endpoints:

#### 1. **Analyse Missing Records**

```bash
GET http://localhost:8001/api/v1/analysis/missing/1
```

Expected response:

```json
{
    "batch_id": 1,
    "batch_name": "daily_orders_2025_11_01",
    "total_expected": 10,
    "total_processed": 7,
    "missing_count": 3,
    "missing_records": [10004, 10006, 10009],
    "processing_rate": 70.0,
    "unexpected_count": 0,
    "unexpected_records": []
}
```

#### 2. **Get Processing Status**

```bash
GET http://localhost:8001/api/v1/analysis/status/1
```

Shows all expected and processed record IDs side by side.

#### 3. **Get Batch Statistics**

```bash
GET http://localhost:8001/api/v1/analysis/statistics/1
```

Shows overall statistics for the batch.

#### 4. **View All Records**

```bash
GET http://localhost:8001/api/v1/records/batch/1
```

Shows all 17 records (10 expected + 7 processed).

#### 5. **View Only Expected Records**

```bash
GET http://localhost:8001/api/v1/records/batch/1/status/expected
```

Shows the 10 orders that should have been processed.

#### 6. **View Only Processed Records**

```bash
GET http://localhost:8001/api/v1/records/batch/1/status/processed
```

Shows the 7 orders that were actually shipped.

### Clear Data

To remove all sample data:

```bash
curl -X DELETE http://localhost:8001/api/v1/batches/1
```

Or use the Swagger UI at http://localhost:8001/docs

## Real-World Application

This sample data represents common scenarios in data pipelines:

**Use Cases:**

-   📦 **Order fulfillment tracking** - Which orders didn't ship?
-   💳 **Payment processing** - Which transactions failed?
-   📄 **File processing** - Which files weren't processed?
-   🚚 **Shipment tracking** - Which shipments are stuck?
-   📊 **ETL pipelines** - Which records didn't load?

**Business Impact:**
The 3 missing orders represent:

-   $320.00 + $450.00 + $150.00 = **$920.00 in revenue at risk**
-   **3 customers** with unfulfilled orders
-   **70% processing rate** needs investigation

This is exactly what the API helps you identify and monitor! 🔍
