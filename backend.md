# Foresta - Backend System Documentation

## Technology Stack

*   **Framework:** Flask (Python 3.8+)
*   **Database:** SQLite (for development/simplicity), PostgreSQL (recommended for production scalability, especially with geospatial data)
*   **ORM:** SQLAlchemy with Flask-SQLAlchemy
*   **Authentication:** JWT (JSON Web Tokens) via Flask-JWT-Extended
*   **API Handling:** Flask Blueprints, Flask-RESTful (Optional, for structured resources)
*   **CORS:** Flask-CORS
*   **External API Interaction:** `requests` (for OSM Overpass), `earthengine-api` (for Google Earth Engine)
*   **Schema Validation:** Marshmallow (Optional, for request/response validation)
*   **Asynchronous Tasks:** Celery with Redis/RabbitMQ (Optional, recommended for GEE processing to avoid blocking API requests)

## Overview
The Foresta backend provides a RESTful API service that enables the frontend to manage conservation areas, process geospatial data, store species identification results, and handle sensor data from Guardian devices. It serves as the central data repository and processing layer for the entire system.

## Core Backend Responsibilities

1.  **API Layer:** Provides RESTful endpoints for frontend interaction and sensor data ingestion. Handles request parsing, authentication, and response formatting.
2.  **Service Layer:** Encapsulates business logic:
    *   User management (registration, authentication).
    *   Area creation logic (interacting with OSM Overpass API via `requests`).
    *   GEE analysis triggering and data retrieval (using `earthengine-api`).
    *   Storing Species ID results received from the frontend.
    *   Processing and storing incoming Guardian sensor data/alerts.
    *   Database interactions via models.
    *   Authorization checks (ensuring users access only their own data).
3.  **Model Layer:** Defines database table structures using SQLAlchemy ORM (`Users`, `Areas`, `SpeciesIdentifications`, `Sensors`, `Alerts`, `SensorReadings`).
4.  **Authentication & Authorization:** Manages user login/registration, issues JWT tokens, protects API endpoints, and verifies resource ownership.
5.  **External API Integration:** Securely handles communication with OSM Overpass and Google Earth Engine.
6.  **Sensor Data Ingestion:** Provides a dedicated endpoint to receive, validate, and process data from Guardian sensor devices (real or simulated).

## API Endpoints

*Base URL:* `/api`

### Authentication (`/api/auth`)

*   `POST /register`: Creates a new user account.
    *   Request Body: `{ "full_name": "...", "email": "...", "password": "..." }`
    *   Response: `201 Created` or error message.
*   `POST /login`: Authenticates a user and returns JWT tokens.
    *   Request Body: `{ "email": "...", "password": "..." }`
    *   Response: `200 OK` with `{ "access_token": "...", "refresh_token": "..." }` or `401 Unauthorized`.
*   `POST /refresh`: Issues a new access token using a valid refresh token. (Requires `Authorization: Bearer <refresh_token>` header)
    *   Response: `200 OK` with `{ "access_token": "..." }`.
*   `GET /profile`: Retrieves the profile of the currently authenticated user. (Requires `Authorization: Bearer <access_token>` header)
    *   Response: `200 OK` with user details `{ "id": ..., "full_name": "...", "email": "..." }`.
*   `PUT /profile`: Updates the profile of the currently authenticated user. (Requires `Authorization: Bearer <access_token>` header)
    *   Request Body: `{ "full_name": "..." }` (Password change likely needs separate endpoint)
    *   Response: `200 OK` with updated user details.

### Areas (`/api/areas`)

*   `POST /`: Creates a new conservation area for the authenticated user.
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Request Body: `{ "name": "Selected Area Name", "osm_id": ..., "osm_type": "way/relation/node" }` (Data from frontend OSM Nominatim selection)
    *   Backend Logic:
        1.  Verify authentication.
        2.  Call OSM Overpass service to get `boundary_coordinates` using `osm_id` and `osm_type`.
        3.  Save new `Area` record to DB (linking `user_id`, name, OSM details, boundaries).
        4.  (Optional/Async) Trigger GEE analysis service using boundaries. Update record later.
    *   Response: `201 Created` with new area details `{ "id": ..., "name": "...", ... }` or error.
*   `GET /`: Retrieves a list of all areas belonging to the authenticated user.
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Backend Logic: Query `Areas` table filtered by `user_id`.
    *   Response: `200 OK` with `[ { "id": ..., "name": "...", ... }, ... ]`.
*   `GET /<int:area_id>`: Retrieves detailed information for a specific area owned by the user.
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Backend Logic: Query `Areas` table for `area_id`, **verify `user_id` matches authenticated user**. Include GEE data and boundary coordinates.
    *   Response: `200 OK` with full area details or `404 Not Found` / `403 Forbidden`.
*   `PUT /<int:area_id>`: Updates basic information (e.g., name) for a specific area.
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Request Body: `{ "name": "New Area Name" }`
    *   Backend Logic: Find area, verify ownership, update record.
    *   Response: `200 OK` with updated area details or `404/403`.
*   `DELETE /<int:area_id>`: Deletes a specific area owned by the user.
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Backend Logic: Find area, verify ownership, delete record (and potentially related data like species IDs, sensor links - depends on cascade rules).
    *   Response: `204 No Content` or `404/403`.

### Species Identification (`/api/areas/<int:area_id>/species`)

*   `POST /`: Saves a species identification result (obtained by the frontend from PlantNet) for a specific area.
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Request Body: `{ "plantnet_result_json": { ... }, "image_url": "..." }`
    *   Backend Logic: Verify user owns `area_id`. Save data to `SpeciesIdentifications` table, linking `user_id`, `area_id`, timestamp, JSON result, and image URL.
    *   Response: `201 Created` with the saved record ID or `404/403`.
*   `GET /history`: Retrieves the paginated history of species identifications made by the user within the specified area.
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Query Params: `?page=1&per_page=10` (for pagination)
    *   Backend Logic: Query `SpeciesIdentifications` table filtered by `area_id` **and** `user_id`. Order by timestamp descending. Apply pagination.
    *   Response: `200 OK` with `{ "identifications": [ {...}, ... ], "total_pages": ..., "current_page": ... }` or `404/403`.

### Sensors & Alerts (`/api/`)

*   `POST /sensors/data`: **Receives** data/alerts from Guardian sensor devices.
    *   **Authentication:** This endpoint needs a strategy for verifying the sender (e.g., pre-shared secret header, device-specific API key/token associated with `code_name`). It's *not* typically protected by user JWT.
    *   Request Body: JSON payload matching `sensor.json` format.
    *   Backend Logic:
        1.  Authenticate/verify sensor.
        2.  Validate JSON payload schema.
        3.  Parse data (`code_name`, `timestamp`, `gps_coordinates`, `environment`, `detections`, etc.).
        4.  Update the corresponding `Sensors` record (`last_seen`, `battery_info`, `status`).
        5.  Store detailed readings in `SensorReadings` if configured.
        6.  Check `detections` confidence scores against thresholds. If exceeded, create a new record in the `Alerts` table.
        7.  (Optional) Trigger real-time notification (e.g., WebSocket).
    *   Response: `202 Accepted` (data received for processing) or `400 Bad Request` / `401 Unauthorized` / `403 Forbidden`.
*   `GET /areas/<int:area_id>/sensors`: Retrieves a list of sensors associated with a specific area owned by the user.
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Backend Logic: Query `Sensors` table filtered by `area_id`, verify user owns the area.
    *   Response: `200 OK` with `[ { "id": ..., "name": ..., "latitude": ..., "longitude": ..., "status": ..., "last_seen": ..., "battery_percentage": ... }, ... ]` or `404/403`.
*   `GET /areas/<int:area_id>/alerts`: Retrieves paginated alerts for a specific area owned by the user.
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Query Params: `?page=1&per_page=15&status=New&type=FIRE` (example filters)
    *   Backend Logic: Query `Alerts` table filtered by `area_id`, verify user owns the area. Apply filters and pagination. Join with `Sensors` table to get sensor name.
    *   Response: `200 OK` with `{ "alerts": [ {...}, ... ], "total_pages": ..., "current_page": ... }` or `404/403`.
*   `PUT /alerts/<string:alert_id>/acknowledge`: Marks a specific alert as acknowledged (or resolved).
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Request Body: `{ "status": "Acknowledged" }` (or "Resolved")
    *   Backend Logic: Find `Alert` by `alert_id`. Verify the associated area belongs to the authenticated user. Update the alert's `status`.
    *   Response: `200 OK` with updated alert details or `404/403`.
*   `GET /areas/<int:area_id>/sensors/readings`: (Optional) Retrieves historical time-series data for sensors in an area.
    *   Requires `Authorization: Bearer <access_token>` header.
    *   Query Params: `?metric=temperature&start_time=...&end_time=...&sensor_id=...&aggregation=hour` (example filters/parameters)
    *   Backend Logic: Complex query on `SensorReadings` table, filtered by area (and user ownership), time range, metric type, potentially sensor ID. May involve aggregation.
    *   Response: `200 OK` with time-series data formatted for charting.

## Database Schema (Revised)

*   **Users** (`users`)
    *   `id` (PK, Integer/UUID)
    *   `full_name` (String, Not Null)
    *   `email` (String, Unique, Indexed, Not Null)
    *   `password_hash` (String, Not Null)
    *   `created_at` (DateTime, Default=Now)
    *   `areas` (Relationship backref to `Area`)
    *   `species_identifications` (Relationship backref to `SpeciesIdentification`)
*   **Areas** (`areas`)
    *   `id` (PK, Integer/UUID)
    *   `user_id` (FK referencing `users.id`, Indexed, Not Null)
    *   `name` (String, Not Null)
    *   `osm_id` (BigInteger, Nullable)
    *   `osm_type` (String, Nullable)
    *   `boundary_coordinates` (Text/JSON/GeoAlchemy2 Geometry, Nullable) - *Store as GeoJSON string or use PostGIS*
    *   `gee_tree_loss_percentage` (Float, Nullable)
    *   `gee_tree_gain_percentage` (Float, Nullable)
    *   `gee_deforestation_trends` (Text/JSON, Nullable) - *Store JSON string*
    *   `created_at` (DateTime, Default=Now)
    *   `last_updated` (DateTime, On Update=Now)
    *   `user` (Relationship to `User`)
    *   `species_identifications` (Relationship backref to `SpeciesIdentification`)
    *   `sensors` (Relationship backref to `Sensor`)
    *   `alerts` (Relationship backref to `Alert`)
*   **SpeciesIdentifications** (`species_identifications`)
    *   `id` (PK, Integer/UUID)
    *   `user_id` (FK referencing `users.id`, Indexed, Not Null)
    *   `area_id` (FK referencing `areas.id`, Indexed, Not Null)
    *   `timestamp` (DateTime, Indexed, Default=Now)
    *   `image_url` (String, Not Null) - *URL to image stored in cloud storage*
    *   `plantnet_result_json` (Text/JSON, Not Null)
    *   `best_match_name` (String, Indexed, Nullable) - *Extracted for display*
    *   `score` (Float, Nullable) - *Extracted for display*
    *   `user` (Relationship to `User`)
    *   `area` (Relationship to `Area`)
*   **Sensors** (`sensors`)
    *   `id` (PK, String/UUID) - *Use `code_name` if unique and suitable, otherwise UUID*
    *   `code_name` (String, Unique, Indexed, Not Null) - *The identifier sent by the device*
    *   `area_id` (FK referencing `areas.id`, Indexed, Not Null)
    *   `name` (String, Nullable) - *User-friendly name, defaulting to `code_name`*
    *   `latitude` (Float, Not Null)
    *   `longitude` (Float, Not Null)
    *   `type` (String, Default="GuardianV1")
    *   `status` (String, Default="Unknown", Indexed) - e.g., "Online", "Offline", "Error"
    *   `last_seen` (DateTime, Nullable, Indexed)
    *   `battery_percentage` (Float, Nullable)
    *   `installation_date` (DateTime, Nullable)
    *   `created_at` (DateTime, Default=Now)
    *   `area` (Relationship to `Area`)
    *   `alerts` (Relationship backref to `Alert`)
    *   `readings` (Relationship backref to `SensorReading`) - *If storing readings*
*   **Alerts** (`alerts`)
    *   `id` (PK, String/UUID) - *Use `alert_id` from sensor if provided and unique, otherwise generate UUID*
    *   `sensor_code_name` (FK referencing `sensors.code_name`, Indexed, Not Null) - *Link via code_name*
    *   `area_id` (FK referencing `areas.id`, Indexed, Not Null) - *Denormalized for easier querying*
    *   `timestamp` (DateTime, Indexed, Not Null) - *Time of the event*
    *   `alert_type` (String, Indexed, Not Null) - e.g., "FIRE_DETECTED", "LOGGING_DETECTED", "LOW_BATTERY", "OFFLINE"
    *   `details_json` (Text/JSON, Nullable) - *Store `detections` block or other relevant context*
    *   `status` (String, Indexed, Default="New") - e.g., "New", "Acknowledged", "Resolved"
    *   `created_at` (DateTime, Default=Now)
    *   `sensor` (Relationship to `Sensor`)
    *   `area` (Relationship to `Area`)
*   **SensorReadings** (`sensor_readings`) - *Optional table for historical data*
    *   `id` (PK, BigInteger/UUID)
    *   `sensor_code_name` (FK referencing `sensors.code_name`, Indexed, Not Null)
    *   `timestamp` (DateTime, Indexed, Not Null)
    *   `temperature` (Float, Nullable)
    *   `humidity` (Float, Nullable)
    *   `smoke_level` (Float, Nullable)
    *   # Add other relevant readings columns
    *   `sensor` (Relationship to `Sensor`)
    *   *(Composite index on `(sensor_code_name, timestamp)` recommended)*

## Authentication & Authorization

*   **Authentication:** Uses `Flask-JWT-Extended` to handle login and token generation (access + refresh). Tokens are expected in the `Authorization: Bearer <token>` header for protected endpoints.
*   **Authorization:** **CRITICAL:** All API endpoints operating on specific resources (Areas, Species IDs, Sensors, Alerts) **MUST** verify that the resource belongs to the authenticated user (`user_id` from JWT matches `user_id` on the resource or its parent Area). This prevents users from accessing or modifying data that isn't theirs. Queries should typically include a `filter_by(user_id=current_user_id)` clause.

## External API Integration Logic

*   **OSM Overpass (Boundary Fetching):**
    *   Located in: `app/services/osm_service.py` (or similar).
    *   Uses the `requests` library to POST Overpass QL queries (based on `boundary_finder.py` logic) to the Overpass API endpoint.
    *   Requires careful error handling (timeouts, HTTP errors, empty responses) and potentially respecting API usage limits with delays if making batch requests.
    *   Parses the JSON response to extract coordinate lists.
*   **Google Earth Engine (GEE Analysis):**
    *   Located in: `app/services/gee_service.py` (or similar).
    *   Uses the `earthengine-api` library.
    *   Requires initialization with Service Account credentials (path/details read from environment variables/config).
    *   Takes boundary coordinates as input to define the `ee.Geometry`.
    *   Executes GEE computations (based on `gee.py` logic) for loss%, gain%, and trends.
    *   Uses `.getInfo()` to retrieve results from GEE servers.
    *   **Recommendation:** Run GEE tasks asynchronously (e.g., using Celery) as they can be time-consuming and block API responses. The API endpoint could return `202 Accepted` and update the Area record later.

## Sensor Data Handling (`/api/sensors/data`)

1.  **Receive Request:** Endpoint accepts POST requests with JSON body.
2.  **Authenticate Sensor:** Implement mechanism (e.g., API key header check tied to `code_name`) to verify the request origin. Return `401/403` if invalid.
3.  **Validate Payload:** Check if the JSON matches the expected `sensor.json` structure (required fields, data types). Return `400 Bad Request` if invalid.
4.  **Find/Update Sensor Record:** Use `code_name` to find the `Sensor` in the database. Update its `last_seen`, `status`, `battery_percentage`, and potentially GPS coordinates. If the sensor doesn't exist, consider auto-registering it (requires an associated `area_id` which might need to be inferred or pre-configured) or reject the data.
5.  **Store Readings (Optional):** If configured, save timestamped `temperature`, `humidity`, etc., to the `SensorReadings` table.
6.  **Check for Alerts:** Evaluate `detections` block (e.g., `fire.confidence > 0.8`, `logging.confidence > 0.7`).
7.  **Create Alert Record:** If thresholds are met, create a new entry in the `Alerts` table with `sensor_code_name`, inferred `area_id`, `timestamp`, `alert_type`, and `details_json`.
8.  **Trigger Notifications (Optional):** If an alert is created, push a message via WebSockets or another mechanism to notify relevant frontend clients.
9.  **Respond:** Return `202 Accepted`.

## File Structure (Recommended)

## Project Structure
```
/backend
├── app/ # Main application package
│ ├── api/ # API Blueprints (Flask routes)
│ │ ├── init.py
│ │ ├── auth_routes.py
│ │ ├── area_routes.py
│ │ ├── species_routes.py
│ │ └── sensor_routes.py
│ ├── models/ # SQLAlchemy ORM models
│ │ ├── init.py
│ │ ├── user.py
│ │ ├── area.py
│ │ ├── species_id.py
│ │ ├── sensor.py
│ │ └── alert.py
│ ├── services/ # Business logic layer
│ │ ├── init.py
│ │ ├── auth_service.py
│ │ ├── osm_service.py
│ │ ├── gee_service.py
│ │ ├── sensor_service.py
│ │ └── area_service.py
│ ├── utils/ # Helper functions (hashing, validation schemas)
│ │ ├── init.py
│ │ └── helpers.py
│ ├── init.py # Application factory (create_app)
│ ├── config.py # Configuration classes (Development, Production, Testing)
│ └── database.py # SQLAlchemy setup (db object)
├── migrations/ # Flask-Migrate files (if used)
├── tests/ # Unit and integration tests
├── instance/ # Instance-specific config, SQLite DB file (GITIGNORE)
│ └── foresta.db
├── .env # Environment variables (GITIGNORE)
├── .flaskenv # Environment variables for Flask CLI (e.g., FLASK_APP, FLASK_ENV)
├── requirements.txt # Python dependencies
└── run.py # Script to run the development server (imports create_app)
```

## Local Development Setup

1.  **Navigate to Backend Directory:**
    ```bash
    cd foresta-app/backend
    ```
2.  **Create & Activate Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # .\venv\Scripts\activate  # Windows
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment:**
    *   Create a `.env` file in the `backend` directory.
    *   Add necessary variables:
        ```dotenv
        FLASK_APP=run.py
        FLASK_ENV=development
        SECRET_KEY=your_super_secret_flask_key_here # Used for session signing etc.
        JWT_SECRET_KEY=your_super_secret_jwt_key_here # Used for JWT signing
        DATABASE_URL=sqlite:///../instance/foresta.db # Path to SQLite DB in instance folder
        # GEE Credentials (adjust path if necessary)
        GEE_SERVICE_ACCOUNT_EMAIL=school@foresta-456412.iam.gserviceaccount.com
        GEE_KEY_FILE_PATH=../important_scripts/data_artifacts/foresta-456412-17f5747ef974.json
        # Optional: CORS allowed origins
        CORS_ORIGINS=http://localhost:5173 # Frontend URL
        # Optional: Sensor API Key (example)
        # SENSOR_API_KEY=a_secret_key_for_guardian_devices
        ```
    *   Create an `.flaskenv` file (optional, helps Flask CLI):
        ```dotenv
        FLASK_APP=run.py
        FLASK_ENV=development
        ```
5.  **Initialize Database (if using Flask-Migrate):**
    ```bash
    # One time only:
    # flask db init
    # flask db migrate -m "Initial database schema."
    flask db upgrade # Apply migrations
    ```
    *If not using Flask-Migrate, the tables might be created automatically by SQLAlchemy on first run if configured.*

6.  **Run the Development Server:**
    ```bash
    flask run
    # Or: python run.py
    ```
    *The backend should be running, typically on `http://localhost:5000`.*

## Key Dependencies

*   `Flask`: Web framework.
*   `Flask-SQLAlchemy`: ORM integration.
*   `Flask-JWT-Extended`: JWT authentication handling.
*   `Flask-CORS`: Cross-Origin Resource Sharing handling.
*   `Flask-Migrate` (Optional): Database schema migrations via Alembic.
*   `SQLAlchemy`: Core ORM.
*   `psycopg2-binary` (If using PostgreSQL): Database driver.
*   `python-dotenv`: Loading `.env` files.
*   `requests`: Making HTTP requests (to OSM Overpass).
*   `earthengine-api`: Google Earth Engine Python client.
*   `werkzeug`: WSGI utility library (includes password hashing).

## Potential Challenges & Considerations

*   **CORS:** Ensure `Flask-CORS` is configured correctly, especially for production (don't allow `*`).
*   **Authentication:** Securely manage JWT secrets. Implement refresh token logic correctly.
*   **Authorization:** Rigorously enforce user ownership checks in all relevant API endpoints.
*   **GEE Performance & Quotas:** GEE tasks can be slow. Use asynchronous task queues (Celery) for GEE analysis. Monitor GEE quotas. Handle `ee.EEException` errors.
*   **OSM Overpass API Limits:** Be respectful of the public Overpass API. Implement delays if making many requests. Consider hosting your own instance for heavy use. Handle request errors gracefully.
*   **Database Performance:** Index frequently queried columns (FKs, timestamps, status, user\_id, area\_id). Use appropriate data types (JSONB/Geometry in PostgreSQL). Implement pagination for large datasets.
*   **Sensor Authentication:** Decide on and implement a secure method for authenticating incoming sensor data.
*   **Error Handling:** Implement comprehensive error handling and logging throughout the application. Return meaningful HTTP status codes and error messages.
*   **Scalability:** SQLite is simple but limits concurrency. Plan for PostgreSQL if scaling is anticipated. Asynchronous tasks are key for scaling operations like GEE analysis.
*   **Configuration Management:** Use environment variables (`.env`) and Flask's config objects (`config.py`) effectively to manage settings for different environments (dev, prod). **Never commit secrets to Git.**

---
