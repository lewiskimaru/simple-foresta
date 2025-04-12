# Foresta Project

## Overview
Foresta is an advanced forest management system that integrates AI, software, and hardware solutions to monitor and manage forests and environmental areas. The platform provides tools for area management, species identification, and environmental monitoring through Guardian sensors.

## Core Features

| **Category**               | **Feature**                | **Capabilities**                                                                 | **Dependencies**                                                                 |
|----------------------------|----------------------------|----------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Geospatial Intelligence** |                            |                                                                                  |                                                                                  |
|                            | Boundary Management        | - OSM-based location search<br>- Polygon coordinate extraction<br>- Area metrics | OpenStreetMap (Nominatim/Overpass), Frontend location search, Backend boundary extraction |
|                            | Satellite Analysis         | - Tree loss/gain percentages<br>- Annual deforestation trends                    | Google Earth Engine, Backend processing                                          |
| **Species Identification**  |                            |                                                                                  |                                                                                  |
|                            | AI Recognition             | - Plant identification from images<br>- Identification history                  | PlantNet API (frontend integration), Database storage                            |
| **Guardian Sensor Network** |                            |                                                                                  |                                                                                  |
|                            | Real-Time Monitoring       | - Fire/logging detection<br>- Environmental condition tracking                   | Sensor simulation script, MQTT protocol, Backend API endpoints                    |
|                            | Device Management          | - Battery health alerts<br>- GPS mapping                                         | Sensor simulation, Backend processing                                            |
| **Technical Architecture**  |                            |                                                                                  |                                                                                  |
|                            | Frontend                   | - Landing page<br>- User dashboard<br>- Area dashboard<br>- SpeciesID dashboard<br>- Interactive maps     | React, Vite, Axios, Leaflet/Mapbox                                               |
|                            | Backend                    | - API endpoints<br>- Data processing<br>- Authentication                         | Flask, SQLAlchemy, JWT                                                           |
| **Security**                |                            |                                                                                  |                                                                                  |
|                            | Authentication             | - User registration/login<br>- JWT token management                              | PBKDF2-SHA256 hashing, JWT                                                        |
| **External Integrations**   |                            |                                                                                  |                                                                                  |
|                            | APIs                       | - PlantNet species ID<br>- Google Earth Engine                                   | API keys, Service accounts                                                       |

## User Flow

1. **Landing Page**
   - User arrives at landing page describing Foresta project
   - Options to sign up or log in

2. **Authentication**
   - User registers or logs in
   - JWT token generated for session management

3. **Main Dashboard**
   - User sees list of the areas they already registered, if none then they see blank screen
   - Option to create new areas on the top bar
   - Top Navigation bar Only: Foresta logo, Notifications, Account

4. **Area Creation**
   - User enters area name/location
   - Frontend searches OSM for matching areas
   - User selects area from results
   - User adds a description
   - User clicks save
   - App sends area information to Backend
   - Backend extracts boundary coordinates from OSM
   - Area saved to database

5. **Area Dashboard**
   - When user clicks on an area on the main dashboard they are directed to the area's dashboard 
   - Sidebar navigation: Home, Species ID, Guardian
   - Top bar: Foresta logo, Notifications, Account
   - Page shows area statistics and map

6. **Species Identification**
   - User uploads image(s)
   - Frontend sends image to PlantNet API
   - Results displayed and stored in database
   - Identification history shown below the upload and results widget

7. **Guardian Monitoring**
   - Dashboard displays sensor data
   - Alert history and sensor status
   - Map showing sensor locations within area

## Project Structure
```
/foresta-app
├── /frontend                   # React frontend (Vite)
│   ├── /public                 # Static assets
│   ├── /src                    
│   │   ├── /components         # UI components
│   │   │   ├── /auth           # Authentication components
│   │   │   ├── /dashboard      # Dashboard components
│   │   │   ├── /species        # Species identification components
│   │   │   ├── /guardian       # Guardian sensor components
│   │   │   └── /common         # Shared components
│   │   ├── /contexts           # React contexts
│   │   ├── /hooks              # Custom hooks
│   │   ├── /pages              # Page components
│   │   ├── /services           # API services
│   │   ├── /utils              # Utility functions
│   │   ├── App.jsx             # Main application
│   │   ├── main.jsx            # Entry point
│   │   └── axios.js            # Axios configuration
│   ├── index.html              # HTML template
│   ├── vite.config.js          # Vite configuration
│   └── package.json            # Frontend dependencies
├── /backend                    # Flask backend
│   ├── /routes                 # API routes
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── areas.py            # Area management endpoints
│   │   ├── species.py          # Species identification endpoints
│   │   ├── sensors.py          # Guardian sensor endpoints
│   │   └── alerts.py           # Alert management endpoints
│   ├── /models                 # Database models
│   │   ├── user.py             # User model
│   │   ├── area.py             # Area model
│   │   ├── species.py          # Species model
│   │   ├── sensor.py           # Sensor model
│   │   └── alert.py            # Alert model
│   ├── /services               # Business logic
│   │   ├── auth_service.py     # Authentication logic
│   │   ├── area_service.py     # Area management logic
│   │   ├── species_service.py  # Species identification logic
│   │   ├── sensor_service.py   # Sensor data processing
│   │   └── osm_service.py      # OpenStreetMap integration
│   ├── /utils                  # Utility functions
│   │   ├── gee_client.py       # Google Earth Engine client
│   │   └── db_helper.py        # Database utilities
│   ├── app.py                  # Main Flask application
│   ├── config.py               # Configuration settings
│   └── requirements.txt        # Backend dependencies
├── /scripts                    # Helper scripts
│   ├── sensor_simulator.py     # Guardian sensor simulator
│   └── db_init.py              # Database initialization
├── README.md                   # Project documentation
└── run.py                      # Application entry point
```

## Database Schema

### User
- `id` (PK): Integer
- `username`: String
- `email`: String (unique)
- `password_hash`: String
- `created_at`: DateTime

### Area
- `id` (PK): Integer
- `name`: String
- `user_id` (FK): Integer (references User.id)
- `boundaries`: JSON (GeoJSON polygon)
- `size`: Float (hectares)
- `type`: String
- `created_at`: DateTime
- `description`: Text

### Species
- `id` (PK): Integer
- `area_id` (FK): Integer (references Area.id)
- `scientific_name`: String
- `common_name`: String
- `confidence_score`: Float
- `identified_at`: DateTime
- `image_url`: String
- `plant_net_response`: JSON
- `notes`: Text

### Sensor
- `id` (PK): Integer
- `area_id` (FK): Integer (references Area.id)
- `type`: String
- `location`: JSON (coordinates)
- `status`: String
- `last_reading`: DateTime
- `installation_date`: DateTime

### Alert
- `id` (PK): Integer
- `sensor_id` (FK): Integer (references Sensor.id)
- `area_id` (FK): Integer (references Area.id)
- `type`: String
- `timestamp`: DateTime
- `data`: JSON
- `status`: String

## API Endpoints

### Authentication
- `POST /api/auth/register`: Create new account
- `POST /api/auth/login`: Authenticate and get token
- `GET /api/auth/profile`: Get current user profile

### Areas
- `GET /api/areas`: List user's areas
- `POST /api/areas`: Create new area
- `GET /api/areas/:id`: Get area details
- `PUT /api/areas/:id`: Update area
- `DELETE /api/areas/:id`: Remove area
- `GET /api/areas/:id/statistics`: Get area metrics from Google Earth Engine

### Location Search
- `GET /api/location/search?q=:query`: Search locations using OSM
- `GET /api/location/:osm_id/boundary`: Get boundary coordinates for OSM location

### Species
- `POST /api/species/save-identification`: Save plant identification results
- `GET /api/areas/:id/species`: Get identification history for area

### Sensors (Guardian)
- `GET /api/areas/:id/sensors`: List sensors in area
- `POST /api/areas/:id/sensors`: Register new sensor
- `GET /api/sensors/:id`: Get sensor details
- `GET /api/sensors/:id/data`: Get sensor readings
- `POST /api/sensors/data`: Receive data from Guardian devices
- `GET /api/areas/:id/alerts`: Get alerts for area

## Data Flow

### Area Creation
1. Frontend sends location search query to backend
2. Backend queries OSM Nominatim API for location matches
3. Frontend displays results to user
4. User selects location
5. Backend queries OSM Overpass API for boundary coordinates
6. Area data saved to database
7. Google Earth Engine analysis requested for the area

### Species Identification
1. User uploads image in frontend
2. Frontend calls PlantNet API directly with image
3. Frontend displays identification results
4. Frontend sends identification results to backend
5. Backend saves results to database
6. Frontend requests identification history from backend
7. Backend returns history from database

### Guardian Sensor Monitoring
1. Sensors (or simulator) send data to backend API
2. Backend processes and stores sensor readings
3. Backend generates alerts based on thresholds
4. Frontend polls for sensor data and alerts
5. Frontend displays real-time data and alerts

## Setup and Installation

### Prerequisites
- Node.js (v16+)
- Python (v3.9+)
- npm or yarn
- pip

### Installation

1. **Clone the repository**:
   ```
   git clone https://github.com/yourusername/foresta.git
   cd foresta
   ```

2. **Backend setup**:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   pip install -r requirements.txt
   cd ..
   ```

3. **Frontend setup**:
   ```
   cd frontend
   npm install  # or yarn install
   cd ..
   ```

4. **Environment configuration**:
   - Create `.env` files for both frontend and backend with necessary API keys
   - Configure Google Earth Engine credentials

5. **Database initialization**:
   ```
   python scripts/db_init.py
   ```

### Running the Application

1. **Start the backend**:
   ```
   python run.py
   ```
   The backend will be available at http://localhost:5001

2. **Start the frontend (in a separate terminal)**:
   ```
   cd frontend
   npm run dev  # or yarn dev
   ```
   The frontend will be available at http://localhost:5173

3. **Start the sensor simulator (optional)**:
   ```
   python scripts/sensor_simulator.py
   ```

## Common Issues and Troubleshooting

### CORS Issues
- **Symptoms**: Frontend unable to communicate with backend, browser console shows CORS errors
- **Solution**: 
  ```python
  # In backend/app.py
  from flask_cors import CORS
  
  app = Flask(__name__)
  CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}},
       supports_credentials=True)
  ```

### Port Conflicts
- **Symptoms**: "Address already in use" error when starting the backend
- **Solution**: Change the default port in `run.py`:
  ```python
  app.run(host='0.0.0.0', port=5001, debug=True)
  ```

### Authentication Issues
- **Symptoms**: "Invalid token" or "Unauthorized" errors
- **Solution**: Check JWT configuration and ensure token is properly passed in requests:
  ```javascript
  // In frontend/src/axios.js
  axios.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  ```

### API Endpoint Issues
- **Symptoms**: 404 errors when accessing API endpoints
- **Solution**: Double-check API URL configuration and route definitions

### Frontend-Backend Communication
- **Symptoms**: Frontend unable to fetch data from backend
- **Solution**: Use Vite's proxy configuration for development:
  ```javascript
  // In vite.config.js
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true
      }
    }
  }
  ```

## Guardian Sensor Simulation

For development and testing purposes, a sensor simulator is provided that mimics the behavior of real Guardian sensors:

```python
# Sample code from scripts/sensor_simulator.py
import requests
import json
import time
import random
from datetime import datetime

# Configuration
API_URL = "http://localhost:5001/api/sensors/data"
AREA_ID = 1  # Default area ID for testing

def generate_sensor_reading(sensor_id, area_id):
    """Generate a simulated sensor reading"""
    reading = {
        "sensor_id": sensor_id,
        "area_id": area_id,
        "timestamp": datetime.now().isoformat(),
        "readings": {
            "temperature": round(random.uniform(15, 35), 2),
            "humidity": round(random.uniform(30, 90), 2),
            "smoke_level": round(random.uniform(0, 0.2), 3),
            "sound_level": round(random.uniform(30, 70), 2)
        },
        "status": {
            "battery": round(random.uniform(60, 100), 2),
            "system_health": "good",
            "gps": {
                "latitude": 36.821528 + random.uniform(-0.005, 0.005),
                "longitude": -1.292066 + random.uniform(-0.005, 0.005)
            }
        }
    }
    
    # Occasionally generate an alert
    if random.random() < 0.1:  # 10% chance
        alert_type = random.choice(["fire", "logging"])
        if alert_type == "fire":
            reading["alert"] = {
                "type": "fire",
                "level": "high",
                "smoke_level": round(random.uniform(0.8, 1.0), 3)
            }
        else:
            reading["alert"] = {
                "type": "logging",
                "level": "medium",
                "audio_signature": "chainsaw_detected",
                "confidence": round(random.uniform(0.7, 0.95), 3)
            }
    
    return reading

def simulate_sensor(sensor_id, area_id, interval=60):
    """Send simulated sensor data at regular intervals"""
    while True:
        reading = generate_sensor_reading(sensor_id, area_id)
        try:
            response = requests.post(API_URL, json=reading)
            print(f"Sent data for sensor {sensor_id}: {response.status_code}")
            print(json.dumps(reading, indent=2))
        except Exception as e:
            print(f"Error sending data: {e}")
        
        time.sleep(interval)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Guardian Sensor Simulator")
    parser.add_argument("--sensor", type=int, default=1, help="Sensor ID to simulate")
    parser.add_argument("--area", type=int, default=AREA_ID, help="Area ID")
    parser.add_argument("--interval", type=int, default=60, help="Interval in seconds")
    
    args = parser.parse_args()
    
    print(f"Starting Guardian Sensor Simulator for sensor {args.sensor} in area {args.area}")
    print(f"Sending data every {args.interval} seconds")
    print("Press Ctrl+C to stop")
    
    simulate_sensor(args.sensor, args.area, args.interval)
```

## External API Integration

### PlantNet API
- **Integration**: Directly from frontend to avoid image transfer overhead
- **API Key**: Stored in frontend environment variables
- **Usage**: Image uploads for plant identification

### OpenStreetMap
- **Integration**: Backend integration for location search and boundary extraction
- **Usage**: Area creation and boundary definition

### Google Earth Engine
- **Integration**: Backend integration for satellite analysis
- **Credentials**: Service account key stored securely
- **Usage**: Forest statistics and deforestation analysis

## License

This project is licensed under the MIT License - see the LICENSE file for details.
