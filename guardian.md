# Guardian Sensor System Documentation

## Overview

The Guardian system is a Raspberry Pi-based environmental monitoring device designed to detect threats to forest areas, including fires and illegal logging activities. Each Guardian device acts as a standalone environmental monitoring station that collects data from multiple sensors, processes it locally, and transmits information to a centralized backend server.

## Hardware Components

### Core Components
- **Raspberry Pi 4** (Recommended: 2GB or 4GB RAM model)
- **Power Supply**:
  - Primary: 5V/3A USB-C power adapter
  - Backup: 10,000mAh Power Bank with USB-C output (for demonstration)
  - *Note: For real deployments, consider solar panels + battery system*
- **SD Card**: 32GB minimum (Class 10) for OS and data storage
- **GPS Module**: NEO-6M GPS or similar (USB or GPIO connection)
- **Weatherproof Enclosure**: IP65 rated (for demo: simple plastic case is sufficient)

### Sensors
- **Temperature/Humidity Sensor**: DHT22 or BME280
- **Smoke Sensor**: MQ-2 Gas Sensor (detects smoke, LPG, propane)
- **Microphone**: USB Microphone with noise cancellation capabilities
- **Optional Additional Sensors**:
  - Flame Sensor (IR-based)
  - Air Quality Sensor (PM2.5/PM10)
  - Light Sensor (to detect time of day, flashlights at night)

### Connectivity
- **Primary**: Wi-Fi (using built-in Raspberry Pi wireless)
- **Alternative Options** (for actual deployment):
  - 4G/LTE USB Modem
  - LoRa for long-range, low-power communication in remote areas

## Software Architecture

### Operating System
- Raspberry Pi OS Lite (Minimal Debian-based OS)

### Core Software Components
1. **Sensor Data Collection Service**
   - Python daemon that polls connected sensors at defined intervals
   - Collects: temperature, humidity, smoke levels, audio samples
   - Stores raw data in a local SQLite database

2. **Audio Classification System**
   - TensorFlow Lite model trained to detect:
     - Chainsaw sounds
     - Vehicle engines
     - Heavy machinery (bulldozers, logging equipment)
   - Runs periodically to analyze audio snippets

3. **Alert Detection System**
   - Rule-based system that analyzes sensor data
   - Triggers alerts based on thresholds:
     - Fire Alert: Combination of high temperature, low humidity, smoke detection
     - Logging Alert: Audio classification confidence above threshold

4. **Data Transmission Service**
   - Manages periodic data uploads to backend
   - Handles immediate alert transmissions
   - Implements retry logic for failed transmissions
   - Compresses data to minimize bandwidth usage

5. **Device Management Service**
   - Monitors system health (CPU temperature, memory usage)
   - Tracks battery levels (if using battery power)
   - Manages safe shutdown if power runs low

### Dependencies
- Python 3.9+
- TensorFlow Lite
- NumPy
- RPi.GPIO
- PyAudio
- Requests (for API communication)

## Data Collection & Processing

### Sensor Polling Frequencies
- Temperature/Humidity: Every 5 minutes
- Smoke Level: Every 1 minute
- Audio Sampling: 10-second clips every 2 minutes
- GPS Location: Once at startup (fixed position)
- System Status: Every 10 minutes

### Data Processing
1. **Temperature/Humidity**:
   - Raw values smoothed using rolling average
   - Anomaly detection based on rapid changes

2. **Smoke Detection**:
   - Calibration period on startup
   - Baseline adjustment based on time of day
   - Multi-level thresholds (warning, alert, critical)

3. **Audio Processing**:
   - Audio normalization and noise filtering
   - Feature extraction for machine learning model
   - Classification with confidence scores
   - Aggregation of multiple samples to reduce false positives

### Alert Generation Logic
- **Fire Alert**: Triggered when:
  - Smoke level > 600 ppm AND
  - Temperature > 38°C AND
  - Humidity < 30%
  
- **Logging Alert**: Triggered when:
  - Audio classification confidence > 0.75 for chainsaw/vehicle/machinery sounds
  - Detection persists across multiple audio samples

## Communication Protocol

### Data Transmission Format (JSON)
```json
{
  "device_info": {
    "code_name": "GUARDIAN-PI-001",
    "timestamp": "2025-04-13T15:30:45Z",
    "gps_coordinates": {
      "latitude": 37.7749,
      "longitude": -122.4194
    },
    "battery": {
      "percentage": 85,
      "charging": false,
      "estimated_runtime_hours": 12
    },
    "status": "ACTIVE"
  },
  "environment": {
    "temperature": 24.5,
    "humidity": 42.3,
    "smoke_level": 120,
    "last_reading_time": "2025-04-13T15:30:00Z"
  },
  "detections": {
    "fire": {
      "detected": false,
      "confidence": 0.02,
      "time_detected": null
    },
    "logging": {
      "detected": true,
      "confidence": 0.83,
      "time_detected": "2025-04-13T15:28:15Z",
      "detection_type": "chainsaw"
    }
  }
}
```

### Communication Schedule
- **Regular Updates**: Every 15 minutes (configurable)
- **Alert Conditions**: Immediate transmission when alert triggered
- **Retry Logic**: Progressive backoff (30s, 1m, 2m, 5m) for failed transmissions

### API Endpoint
- `POST /api/sensors/data`
- Authentication: API key in header (`X-Guardian-API-Key`)
- Response: HTTP 202 Accepted (async processing)

## Deployment

### Setup Process
1. Flash Raspberry Pi OS to SD card
2. Clone Guardian repository
3. Run installation script: `./install_guardian.sh`
4. Configure device settings in `config.yml`:
   - Device code name
   - GPS coordinates
   - Backend API endpoint
   - API key
   - Sensor thresholds
5. Test sensor connections: `python test_sensors.py`
6. Start Guardian service: `sudo systemctl start guardian.service`

### Mounting Considerations
- Place 1-2 meters above ground level
- Ensure ventilation for accurate temperature/humidity readings
- Position microphone with clear line of sound to surroundings
- Protect from direct rainfall while allowing air circulation

### Maintenance
- Regular SD card backups to prevent corruption
- Periodic sensor calibration
- Remote log monitoring

## Demo Configuration

For the class demonstration, a simplified version of the Guardian system will be configured:

1. **Hardware Setup**:
   - Raspberry Pi 4 in clear plastic case
   - DHT22 temperature/humidity sensor
   - MQ-2 smoke sensor
   - USB microphone
   - Power bank for portability

2. **Demo Features**:
   - Real-time sensor readings displayed on LCD/terminal
   - Simulated fire alert (triggered by matches/lighter near smoke sensor)
   - Simulated logging alert (triggered by playing chainsaw audio)
   - Data transmission to backend via Wi-Fi
   - Visualization of received data on web application

3. **Simulation Mode**:
   - Option to run with simulated sensor data for indoor demos
   - Adjustable parameters to force alert conditions

## Implementation Details

### Main System Components

1. **`guardian_service.py`**: Main service coordinator
2. **`sensor_manager.py`**: Handles sensor readings and calibration
3. **`audio_classifier.py`**: Processes audio for logging detection
4. **`alert_detector.py`**: Analyzes sensor data for alert conditions
5. **`data_transmitter.py`**: Manages communication with backend
6. **`system_monitor.py`**: Tracks system health and battery
7. **`config_manager.py`**: Handles configuration and settings

### Sample Code: Alert Detection Logic

```python
def check_fire_alert(temperature, humidity, smoke_level):
    """Determine if current conditions indicate a potential fire."""
    if (temperature > FIRE_TEMP_THRESHOLD and 
        humidity < FIRE_HUMIDITY_THRESHOLD and 
        smoke_level > FIRE_SMOKE_THRESHOLD):
        
        # Double-check with secondary reading after short delay
        time.sleep(10)
        temp2, hum2, smoke2 = get_current_sensor_readings()
        
        if (temp2 > FIRE_TEMP_THRESHOLD and 
            hum2 < FIRE_HUMIDITY_THRESHOLD and 
            smoke2 > FIRE_SMOKE_THRESHOLD):
            
            return True, max(smoke_level, smoke2) / 1000.0  # Confidence based on smoke
    
    return False, 0.0

def check_logging_alert(audio_samples, num_required=3):
    """Analyze audio samples for logging activity."""
    detections = []
    
    for sample in audio_samples[-num_required:]:
        classification, confidence = classify_audio(sample)
        if classification in ['chainsaw', 'vehicle', 'machinery'] and confidence > 0.7:
            detections.append((classification, confidence))
    
    # If we have enough high-confidence detections
    if len(detections) >= num_required * 0.6:
        # Average the confidence scores
        avg_confidence = sum(conf for _, conf in detections) / len(detections)
        # Return most common detection type
        detection_type = Counter(det_type for det_type, _ in detections).most_common(1)[0][0]
        return True, avg_confidence, detection_type
    
    return False, 0.0, None
```

### Sample Code: Data Transmission

```python
def send_data_to_backend(data, retry_attempts=5):
    """Send sensor data and alerts to backend server."""
    headers = {
        'Content-Type': 'application/json',
        'X-Guardian-API-Key': CONFIG['api_key']
    }
    
    for attempt in range(retry_attempts):
        try:
            response = requests.post(
                CONFIG['backend_endpoint'],
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code in (200, 201, 202):
                logger.info(f"Data successfully sent to backend")
                return True
            else:
                logger.warning(f"Backend returned status code {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending data: {e}")
        
        # Exponential backoff
        if attempt < retry_attempts - 1:
            backoff_time = 30 * (2 ** attempt)
            logger.info(f"Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)
    
    logger.critical("Failed to send data after multiple attempts")
    return False
```

## Future Enhancements

- **Solar Power System**: For long-term deployment
- **Camera Module**: For visual confirmation of alerts (triggered by initial detection)
- **Motion Sensors**: To detect human activity
- **Mesh Networking**: Allow Guardians to relay data for each other
- **Edge AI Improvements**: More sophisticated on-device processing
- **Environmental Impact Monitoring**: Track additional parameters like air quality, rainfall

## Troubleshooting

### Common Issues

1. **Sensor Reading Failures**
   - Verify physical connections
   - Check power supply
   - Run `test_sensors.py` to diagnose

2. **Communication Failures**
   - Verify network connectivity
   - Check API endpoint configuration
   - Validate API key

3. **False Alerts**
   - Recalibrate sensors
   - Adjust threshold values in config
   - Update audio classification model

4. **Power Issues**
   - Check battery connections
   - Monitor power consumption
   - Consider reducing polling frequency

### Diagnostic Commands

```bash
# Check system status
sudo systemctl status guardian.service

# View logs
journalctl -u guardian.service -f

# Test sensors
python3 /opt/guardian/test_sensors.py

# Test connectivity
curl -I {backend_endpoint}

# Manual data transmission
python3 /opt/guardian/manual_transmit.py
```

## References

- Raspberry Pi Documentation: [https://www.raspberrypi.com/documentation/](https://www.raspberrypi.com/documentation/)
- DHT22 Sensor Datasheet: [https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf](https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf)
- MQ-2 Sensor Documentation: [https://www.pololu.com/file/0J309/MQ2.pdf](https://www.pololu.com/file/0J309/MQ2.pdf)
- TensorFlow Lite for Audio Classification: [https://www.tensorflow.org/lite/examples/audio_classification/overview](https://www.tensorflow.org/lite/examples/audio_classification/overview)
