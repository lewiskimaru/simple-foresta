# Guardian Sensor Network System

## Overview

The Guardian Sensor Network is a critical component of the Foresta platform that provides real-time environmental monitoring through a distributed network of Raspberry Pi-based sensor devices deployed in forest areas. This document details the complete system architecture, from hardware deployment to data visualization, including communication protocols, security considerations, and user interfaces.

## 1. System Architecture

### 1.1 Hardware Components

Each Guardian device consists of:
- Raspberry Pi (3B+ or newer) as the central processing unit
- GPS module for location tracking
- Temperature and humidity sensors
- Smoke detection sensor for fire monitoring
- Microphone for audio analysis (chainsaw/logging detection)
- Solar panel and battery for power
- 4G/LTE modem or LoRa transceiver for communication

### 1.2 Software Architecture

The Guardian system is built on three main components:
1. **Guardian Device Software**: Python-based application running on Raspberry Pi devices
2. **Backend Server**: Flask-based API handling data reception, processing, and storage
3. **Frontend Dashboard**: React-based web interface for visualization and management

### 1.3 Communication Flow

```
Guardian Device → REST → API Gateway → Backend Services → Database
                                       ↑
                                       ↓
                             Frontend Dashboard ← User
```

## 2. Guardian Device Operation

### 2.1 Boot Sequence

1. Device powers on and initiates the main Guardian script
2. Script checks for local credentials file
   - If no credentials exist, enters Registration Mode
   - If credentials exist, enters Monitoring Mode
3. Establishes connection to the backend using stored credentials

### 2.2 Registration Mode

The registration process follows these steps:

1. **Hardware Identification**
   - Script extracts device UUID from CPU serial in `/proc/cpuinfo`
   - Performs hardware self-check of connected sensors
   - Displays area code prompt on terminal/LCD or Oled screen

2. **User Input**
   - Field technician enters area ID where the Guardian is being deployed
   - Script validates input format

3. **Registration Request**
   - Script prepares registration payload:
     ```json
     {
       "device_uuid": "b8a5c-d9e3f-12345-67890",
       "hardware_specs": {
         "model": "Raspberry Pi 4B",
         "cpu": "ARM Cortex-A72",
         "memory": "4GB"
       },
       "sensor_capabilities": [
         {"type": "temperature", "model": "DHT22", "precision": "±0.5°C"},
         {"type": "humidity", "model": "DHT22", "precision": "±2%"},
         {"type": "smoke", "model": "MQ-2", "sensitivity": "high"},
         {"type": "audio", "model": "MEMS Microphone", "sampling_rate": "44.1kHz"},
         {"type": "gps", "model": "NEO-6M", "precision": "±2.5m"}
       ],
       "firmware_version": "1.2.0",
       "battery_status": 98
     }
     ```
   - Sends registration request to `/api/areas/{area_id}/sensors/register`

4. **Waiting For Approval**
   - Device enters polling mode, checking for approval status every 60 seconds
   - Displays status indicator (LED blinking or terminal message)

5. **Configuration Reception**
   - Upon approval, receives configuration:
     ```json
     {
       "api_key": "gdn_5f6a7b8c9d0e1f2g3h4i5j6k",
       "sensor_id": 42,
       "name": "North Ridge Guardian",
       "endpoint_urls": {
         "data": "https://api.foresta.io/api/sensors/data",
         "health": "https://api.foresta.io/api/sensors/health"
       },
       "reading_intervals": {
         "health_check": 1800,  // 30 minutes in seconds
         "periodic_data": 7200, // 2 hours in seconds
       },
       "thresholds": {
         "temperature_high": 45,
         "temperature_change_rate": 10,
         "smoke_level": 300,
         "audio_confidence": 0.75
       }
     }
     ```
   - Stores configuration securely in encrypted local file

6. **Test Sequence**
   - Runs complete diagnostic on all sensors
   - Collects sample readings
   - Sends test data packet with "test" flag
   - Waits for confirmation

7. **Activation**
   - Receives activation confirmation
   - Sets up systemd service for automatic start on boot (note that the main script is always set to run on boot)
   - Device transitions from "pending" to "active" status on the dashboard

### 2.3 Monitoring Mode

1. **Initialization**
   - Loads stored credentials and configuration
   - Establishes secure connection to backend
   - Obtains GPS coordinates and stores them, the next time it will check for gps data is in like one week to fix time drift and verify location, the reason for this it to save on power
   - Sends initial health check

2. **Periodic Operations**
   - Performs health checks every 30 minutes
   - Collects and transmits complete sensor data every 2 hours (it transmits an average of what happened in the past 2 hours)
   - Continuously monitors for alert conditions
   - Listens for polling requests from backend

3. **Alert Detection**
   - Continuously samples from sensors
   - Runs local processing to identify alert conditions:
     - Fire detection: Smoke level above threshold OR rapid temperature increase
     - Logging detection: Audio analysis for chainsaw/ truck/ human sounds using edge ML model
   - Immediately transmits alerts when detected

4. **Low Power Operation**
   - Monitors battery levels
   - Enters power-saving mode when battery is below 20%
   - Reduces sensor sampling rates and transmission frequency
   - Prioritizes alert detection over periodic data

### 2.4 Troubleshooting Mode

Activated manually or remotely when issues are detected:

1. **Connectivity Testing**
   - Network connectivity verification
   - API endpoint accessibility checks

2. **Sensor Diagnostics**
   - Individual sensor tests
   - Hardware component status reporting

3. **Log Collection**
   - Compiles system logs
   - Transmits diagnostic information when connectivity is restored

## 3. Communication Protocol

### 3.1 Message Types

#### Health Check Message
```json
{
  "message_type": "health_check",
  "device_info": {
    "sensor_id": 42,
    "uuid": "b8a5c-d9e3f-12345-67890",
    "timestamp": "2025-04-13T15:30:45Z"
  },
  "status": {
    "battery": {
      "percentage": 85,
      "charging": true,
      "estimated_runtime_hours": 72
    },
    "connectivity": {
      "signal_strength": 67,
      "network_type": "LTE"
    },
    "storage": {
      "total_mb": 16000,
      "used_mb": 3200
    },
    "cpu_load": 12,
    "memory_used_percentage": 34,
    "uptime_hours": 120
  }
}
```

#### Periodic Data Message
```json
{
  "message_type": "periodic_data",
  "device_info": {
    "sensor_id": 42,
    "uuid": "b8a5c-d9e3f-12345-67890",
    "timestamp": "2025-04-13T16:00:00Z",
    "gps_coordinates": {
      "latitude": 37.7749,
      "longitude": -122.4194,
      "accuracy": 3.5
    },
    "battery": {
      "percentage": 84,
      "charging": true,
      "estimated_runtime_hours": 70
    },
    "status": "ACTIVE"
  },
  "environment": {
    "temperature": 24.5,
    "humidity": 42.3,
    "smoke_level": 12,
    "readings_taken_at": "2025-04-13T15:59:30Z"
  },
  "audio_sampling": {
    "last_detection_run": "2025-04-13T15:55:00Z",
    "detection_results": {
      "chainsaw": 0.02,
      "vehicle": 0.01,
      "human_voices": 0.15,
      "wildlife": 0.78
    }
  }
}
```

#### Alert Message
```json
{
  "message_type": "alert",
  "device_info": {
    "sensor_id": 42,
    "uuid": "b8a5c-d9e3f-12345-67890",
    "timestamp": "2025-04-13T15:28:15Z",
    "gps_coordinates": {
      "latitude": 37.7749,
      "longitude": -122.4194,
      "accuracy": 3.5
    }
  },
  "alert": {
    "type": "logging",
    "subtype": "chainsaw",
    "confidence": 0.92,
    "detection_time": "2025-04-13T15:28:10Z",
    "readings": {
      "audio_amplitude": 65,
      "audio_frequency_pattern": "high_frequency_mechanical",
      "duration_seconds": 15,
      "verification_method": "spectral_analysis"
    }
  }
}
```

### 3.2 Authentication & Security

Every request from the Guardian to the backend includes:

1. **API Key in Header**
   ```
   Authorization: Bearer gdn_5f6a7b8c9d0e1f2g3h4i5j6k
   ```

2. **Message Integrity**
   - HTTPS for all communications
   - Request timestamp included in payload
   - UUID verification against registered devices

3. **Security Measures**
   - API keys stored encrypted on Guardian devices
   - Keys can be revoked remotely if compromise suspected
   - Regular automatic rotation of keys (every 30 days)

## 4. Backend Processing

### 4.1 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/areas/{area_id}/sensors/register` | POST | Register new Guardian device |
| `/api/sensors/data` | POST | Receive sensor data (periodic/alert) |
| `/api/sensors/health` | POST | Receive health check data |
| `/api/sensors/{id}/poll` | GET | Request immediate data update |
| `/api/sensors/{id}/config` | PUT | Update sensor configuration |
| `/api/sensors/{id}/command` | POST | Send command to sensor |
| `/api/areas/{area_id}/sensors` | GET | List all sensors in area |
| `/api/sensors/{id}` | GET | Get sensor details |
| `/api/sensors/{id}/readings` | GET | Get historical sensor readings |
| `/api/sensors/{id}/alerts` | GET | Get alerts for a specific sensor |
| `/api/areas/{area_id}/alerts` | GET | Get all alerts for an area |

### 4.2 Data Processing Pipeline

1. **Ingestion Layer**
   - Validates incoming requests
   - Authenticates API key against database
   - Routes message based on message_type

2. **Processing Layer**
   - Normalizes data formats
   - Validates readings against expected ranges
   - Applies business logic for derived metrics
   - Performs additional alert validation

3. **Storage Layer**
   - Stores processed data in appropriate tables
   - Updates sensor status information
   - Archives historical data

4. **Notification Layer**
   - Generates user notifications for alerts
   - Triggers webhooks for integrated systems
   - Updates real-time dashboard via WebSockets

### 4.3 Database Schema

#### Sensor Table


```sql
CREATE TABLE sensor (
    id SERIAL PRIMARY KEY,
    code_name VARCHAR(50) NOT NULL,
    hardware_uuid VARCHAR(64) NOT NULL UNIQUE,
    area_id INTEGER NOT NULL REFERENCES area(id),
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    battery_percentage DECIMAL(5,2),
    battery_charging BOOLEAN DEFAULT FALSE,
    signal_strength INTEGER,
    firmware_version VARCHAR(20),
    api_key_hash VARCHAR(255),
    installation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_reading_time TIMESTAMP,
    last_health_check TIMESTAMP,
    maintenance_mode BOOLEAN DEFAULT FALSE,
    maintenance_reason TEXT,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### Sensor Reading Table
```sql
CREATE TABLE sensor_reading (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(id),
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    smoke_level INTEGER,
    battery_percentage DECIMAL(5,2),
    battery_charging BOOLEAN,
    estimated_runtime_hours DECIMAL(6,2),
    signal_strength INTEGER,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    audio_detection JSON,
    reading_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### Alert Table
```sql
CREATE TABLE alert (
    id SERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(id),
    area_id INTEGER NOT NULL REFERENCES area(id),
    type VARCHAR(20) NOT NULL,
    subtype VARCHAR(20),
    confidence DECIMAL(4,3),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    detection_time TIMESTAMP NOT NULL,
    resolved_by INTEGER REFERENCES user(id),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    data JSONB, -- Store additional alert-specific data
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 Data Retention Policies

- Health check data: 30 days
- Periodic environmental data: 5 years
- Alert data: Indefinite retention
- Audio detection data: 90 days
- Status change history: Indefinite retention

## 5. Frontend Visualization

### 5.1 Guardian Dashboard Structure

The Guardian dashboard is organized into three main tabs:

#### 5.1.1 Overview Tab

This tab provides a comprehensive view of the Guardian sensor network status:

1. **Network Health Metrics Cards**
   - Total sensors deployed
   - Active/offline/maintenance counts
   - Battery status summary
   - Recent alert count

2. **Recent Alerts Widget**
   - Timeline view of recent alerts (scrollable list)
   - Color-coded by type (red for fire, orange for logging)
   - Status indicators (pending, investigating, resolved)
   - Quick action buttons for alert management

3. **Guardian Map**
   - Interactive map displaying all Guardians in the area
   - Color-coded markers based on status:
     - Green: Active and normal
     - Yellow: Active with low battery
     - Red: Active with alert
     - Gray: Offline
     - Blue: Maintenance mode
   - Clustering for areas with many sensors
   - Click for quick info, double-click for detailed view

4. **Sensor Details Panel**
   - Always Active
   - Seachable dropdown menu to select sensor for viewing
   - Shows latest readings and status
   - Battery and signal strength indicators
   - Recent Alert history for selected sensor
   - Quick action buttons (poll, maintenance mode)

5. **Environmental Data Visualization for selected sensor**
   - Line charts for temperature, humidity, and smoke level
   - Time range selector (24h, 7d, 30d, custom)

#### 5.1.2 Management Tab

This tab provides tools for managing the Guardian sensor network:

1. **Sensor List View**
   - Sortable and filterable table of all sensors
   - Columns: Name, Status, Battery, Last Contact, Alerts, Actions
   - Bulk selection for batch operations
   - Export functionality (CSV, PDF)

2. **Sensor Detail View**
   - Comprehensive information about selected sensor
   - Configuration settings
   - Maintenance history
   - Complete alert history
   - Raw data access

3. **Management Actions**
   - Request immediate data update
   - Toggle maintenance mode
   - Update sensor name/description
   - Change area assignment
   - Decommission sensor

4. **Decommissioning Interface**
   - Reason selection dropdown:
     - End of hardware lifecycle
     - Damaged equipment
     - Area reclassification
     - Legal logging activity
     - Redundant coverage
   - Comment field for additional information
   - Confirmation dialog
   - Option for temporary vs. permanent decommissioning

#### 5.1.3 Information & Setup Tab

This tab provides documentation and setup guidance:

1. **Guardian Information (this is the default view if user has not added any Guardians to the area)**
   - Technical specifications
   - Operational guidelines
   - Maintenance procedures
   - Troubleshooting guides

2. **Setup Instructions**
   - Step-by-step deployment guide
   - Registration process documentation
   - FAQ section

3. **Procurement Interface**
   - Guardian device request form
   - Pricing information
   - Deployment planning calculator
   - Contact information for technical support

### 5.2 Interactive Features

1. **Real-time Updates**
   - Read stored data
   - Push notifications for alerts
   - Automatic dashboard refreshing

2. **Alert Management Workflow**
   - Alert notification display
   - Status transition controls
   - Resolution documentation
   - Action logging

## 6. Implementation Guidelines

### 6.1 Guardian Device Setup

For Raspberry Pi setup:

1. **Autostart Configuration**
   ```
   # Create systemd service file
   sudo nano /etc/systemd/system/guardian.service
   
   # Service file content
   [Unit]
   Description=Guardian Sensor Monitoring Service
   After=network.target
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/guardian
   ExecStart=/usr/bin/python3 /home/pi/guardian/main.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

2. **Main Script Structure**
   ```python
   #!/usr/bin/env python3
   import os
   import sys
   import json
   import time
   import logging
   
   # Set up logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger("guardian")
   
   # Check for credentials
   CREDS_FILE = "/home/pi/guardian/credentials.json"
   
   def main():
       if os.path.exists(CREDS_FILE):
           # Device is registered, start monitoring
           start_monitoring_mode()
       else:
           # Device needs registration
           start_registration_mode()
   
   def start_registration_mode():
       logger.info("Entering registration mode...")
       # Registration logic here
   
   def start_monitoring_mode():
       logger.info("Entering monitoring mode...")
       # Monitoring logic here
   
   if __name__ == "__main__":
       main()
   ```

### 6.2 Backend Implementation

Key considerations for backend implementation:

1. **Performance Optimization**
   - Use asynchronous processing for data ingestion
   - Implement data partitioning for time-series data (can we use comma separation for sensor reading of a single sensor?)

2. **Scalability**
   - Design for horizontal scaling of API servers
   - Use message queue (RabbitMQ, Kafka) for peak handling
   - Implement caching for frequently accessed data

3. **Security**
   - Validate all incoming data against schemas
   - Encrypt sensitive data in transit and at rest

### 6.3 Frontend Implementation

Best practices for the dashboard:

1. **Performance**
   - Use virtualized lists for large sensor datasets
   - Implement progressive loading for historical data
   - Optimize map rendering with clustering

2. **Usability**
   - Design mobile-responsive interface
   - Implement keyboard shortcuts for common actions
   - Provide clear visual feedback for system status

3. **Accessibility**
   - Use ARIA attributes for screen readers
   - Ensure sufficient color contrast
   - Provide alternative text for visual elements

## 7. Testing and Simulation

### 7.1 Guardian Simulator

For development and testing without physical hardware:

1. **Simulator Script**
   ```python
   #!/usr/bin/env python3
   import argparse
   import json
   import random
   import requests
   import time
   from datetime import datetime
   
   def generate_periodic_data(device_id, uuid):
       # Generate realistic sensor readings
       return {
           "message_type": "periodic_data",
           "device_info": {
               "sensor_id": device_id,
               "uuid": uuid,
               "timestamp": datetime.utcnow().isoformat() + "Z",
               "gps_coordinates": {
                   "latitude": 37.7749 + random.uniform(-0.01, 0.01),
                   "longitude": -122.4194 + random.uniform(-0.01, 0.01),
                   "altitude": 120 + random.uniform(-5, 5),
                   "accuracy": random.uniform(2.0, 5.0)
               },
               "battery": {
                   "percentage": random.uniform(70, 100),
                   "charging": random.choice([True, False]),
                   "estimated_runtime_hours": random.uniform(48, 120)
               },
               "status": "ACTIVE"
           },
           "environment": {
               "temperature": random.uniform(20, 30),
               "humidity": random.uniform(30, 60),
               "smoke_level": random.randint(0, 20),
               "readings_taken_at": datetime.utcnow().isoformat() + "Z"
           },
           "audio_sampling": {
               "last_detection_run": datetime.utcnow().isoformat() + "Z",
               "detection_results": {
                   "chainsaw": random.uniform(0, 0.05),
                   "vehicle": random.uniform(0, 0.1),
                   "human_voices": random.uniform(0, 0.2),
                   "wildlife": random.uniform(0.6, 0.9)
               }
           }
       }
   
   def main():
       parser = argparse.ArgumentParser(description='Guardian Simulator')
       parser.add_argument('--devices', type=int, default=3, help='Number of simulated devices')
       parser.add_argument('--interval', type=int, default=60, help='Seconds between data transmissions')
       parser.add_argument('--endpoint', type=str, required=True, help='API endpoint URL')
       parser.add_argument('--api-key', type=str, required=True, help='API key')
       
       args = parser.parse_args()
       
       headers = {
           "Authorization": f"Bearer {args.api_key}",
           "Content-Type": "application/json"
       }
       
       device_ids = list(range(1, args.devices + 1))
       uuids = [f"sim-{d}-{random.randint(10000, 99999)}" for d in device_ids]
       
       print(f"Simulating {args.devices} Guardian devices...")
       
       try:
           while True:
               for i, device_id in enumerate(device_ids):
                   data = generate_periodic_data(device_id, uuids[i])
                   
                   # Random alert generation (5% chance)
                   if random.random() < 0.05:
                       alert_data = generate_alert(device_id, uuids[i])
                       try:
                           resp = requests.post(args.endpoint, json=alert_data, headers=headers)
                           print(f"Alert sent for device {device_id}: {resp.status_code}")
                       except Exception as e:
                           print(f"Error sending alert: {e}")
                   
                   try:
                       resp = requests.post(args.endpoint, json=data, headers=headers)
                       print(f"Data sent for device {device_id}: {resp.status_code}")
                   except Exception as e:
                       print(f"Error sending data: {e}")
               
               time.sleep(args.interval)
       
       except KeyboardInterrupt:
           print("Simulation stopped.")
   
   if __name__ == "__main__":
       main()
   ```

2. **Usage**
   ```bash
   python simulator.py --devices 5 --interval 30 --endpoint http://localhost:5001/api/sensors/data --api-key gdn_5f6a7b8c9d0e1f2g3h4i5j6k
   ```

### 7.2 Testing Scenarios

Common testing scenarios for the Guardian system:

1. **Network Resilience**
   - Simulated connection drops
   - Varying signal strength conditions
   - Data transmission retries

2. **Alert Handling**
   - Fire alert simulation
   - Logging alert simulation
   - Multiple simultaneous alerts

3. **Edge Cases**
   - Battery depletion scenarios
   - Sensor malfunction detection
   - GPS signal loss handling

4. **Load Testing**
   - Maximum supported sensor count
   - Peak data ingestion rates
   - Dashboard performance with large datasets

## 8. Deployment Considerations

### 8.1 Physical Installation

Guidelines for field deployment:

1. **Site Selection**
   - Line of sight for cellular/LoRa connectivity
   - Solar exposure for adequate charging
   - Minimal wildlife interference
   - Strategic coverage of vulnerable areas

2. **Mounting**
   - 3-5 meters above ground level
   - Weather-resistant enclosure
   - Proper ventilation for sensors
   - Secure attachment to prevent theft/damage

3. **Activation**
   - Pre-test all components before field deployment
   - Register device with central system
   - Verify initial data transmission
   - Document precise installation location

### 8.2 Maintenance Schedule

Recommended maintenance procedures:

1. **Regular Checks**
   - Physical inspection every 6 months
   - Cleaning of solar panels and sensors
   - Firmware updates as available
   - Battery replacement every 2 years

2. **Troubleshooting Guidelines**
   - Remote diagnostics when possible
   - Field technician dispatch criteria
   - Common failure modes and solutions
   - Equipment replacement procedures


## 9. Conclusion

The Guardian Sensor Network provides a comprehensive solution for environmental monitoring in forest areas. By integrating hardware sensors, edge computing, and cloud-based analytics, the system enables real-time detection of threats like illegal logging and forest fires. The modular architecture allows for ongoing improvements and adaptations to meet the evolving needs of forest management.

---

**Appendix A: Message Schema Definitions**

Complete JSON schema definitions for all message types.

**Appendix B: API Reference**

Detailed API documentation with request/response examples.

**Appendix C: Hardware Assembly Guide**

Step-by-step instructions for building Guardian devices.
