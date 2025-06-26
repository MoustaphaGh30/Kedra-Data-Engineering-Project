# Google Trends Data Engineering Project

## Key Features

- **API**: A RESTful endpoint (`/trends/{keyword}`) to fetch time series data for any keyword from pytrends library
- **Data Fetching**:
  - Performs an initial fetch of the last 90 days of data for new keywords.
  - I used timeframes for subsequent updates, only fetching data that is missing or was previously incomplete.
- **Proactive Data Maintenance**: A background scheduler runs once every 24 hours to automatically find and update any keywords whose data has not been updated in the last 7 days.
- **Data Integrity**:
  - I Explicitly update incomplete (`isPartial`) data points provided by the Google Trends API.
  - I used Pydantic for data validation and serialization.
  - I enforced data uniqueness at the database level with a `UNIQUE` constraint on keyword and date pairs.

---

## Design Choices

The solution is has multiple layers and offers separation of concerns and maintainability.

#### 1. Container Orchestration
- **`api` service**: A Python container running the FastAPI application.
- **`db` service**: A standard PostgreSQL container for the database.

#### 2. Application Layers (FastAPI)
- **API Layer (`main.py`)**: `/trends/{keyword}` endpoint using FastAPI. It handles request validation, dependency injection (for the database), and response serialization.
- **Service Layer (`services.py`)**: Contains the core business logic.
  - `fetch_and_store_trends()`: Orchestrates fetching logic by determining the correct timeframe and calling the `pytrends` library.
  - `update_stale_keywords_service()`: The function executed by the background job. It queries the database for stale keywords and triggers updates.
- **Data Access Layer (`crud.py`)**: Isolates all database operations. It uses SQLAlchemy to abstract SQL queries, providing functions like `get_stale_keywords` and `bulk_upsert_trend_data`.
- **Scheduler (`main.py` with APScheduler)**: It runs a background job to periodically call the stale keyword update service.

#### 3. Database Schema (`database.py`)
The `trend_data` table is the single source of truth and is defined with the following key columns:
- `date`: The date of the trend data point.
- `keyword`: The keyword being tracked.
- `score`: The interest score (0-100).
- `isPartial`: A boolean flag indicating if the data for that day was incomplete when fetched. This is crucial for knowing when to update a record.
- **`_date_keyword_uc`**: A `UNIQUE` constraint on the combination of `date` and `keyword`, which prevents duplicate entries

---

## Justification for Major Design and Technology Decisions

- **FastAPI**:
    - speed.
    - data validation and serialization powered by Pydantic.
- **APScheduler**: A lightweight, in-process scheduler. It was chosen over a heavier, external system because it fits the requirements of the project.
---

## Setup and Run Instructions

### Running the Application
1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd google-trends-api
    ```

2.  **Build and start the services:**
    ```bash
    docker-compose up --build
    ```
    This command will build the FastAPI image, pull the PostgreSQL image, and start both containers. The `api` service will be available on `http://localhost:8001`.

### Testing the API
- **Swagger UI**: Once the containers are running, open your web browser and navigate to:
  **[http://localhost:8001/docs](http://localhost:8001/docs)**

- **Example Usage**:
  1. Expand the `GET /trends/{keyword}` endpoint.
  2. Click "Try it out".
  3. Enter a keyword and click "Execute".
  4. The first request will fetch and store 90 days of data. Subsequent requests for the same keyword will be much faster and will only fetch new data.

### Accessing the Database
You can connect to the database using any standard PostgreSQL client (like pgAdmin or DBeaver) with the following details:

- **Host**: `localhost`
- **Port**: `5433`
- **Database**: `trends_db`
- **Username**: `user`
- **Password**: `password`
