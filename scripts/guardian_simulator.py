#!/usr/bin/env python3
"""
Guardian Sensor Network Simulator

This script simulates multiple Guardian devices sending sensor data and alerts
to the Foresta backend. It generates realistic environmental data, simulates
battery levels, and occasionally triggers fire or logging alerts.

Usage:
    python guardian_simulator.py --devices 3 --interval 30 --endpoint http://localhost:5000/api/sensors/data

Arguments:
    --devices : Number of Guardian devices to simulate (default: 3)
    --interval : Seconds between regular transmissions (default: 60)
    --endpoint : Backend API endpoint URL (default: http://localhost:5000/api/sensors/data)
    --api-key : API key for authentication (default: demo-key-123)
    --alert-probability : Probability of generating an alert (0-1) (default: 0.1)
    --verbose : Enable verbose logging (default: False)
"""

import argparse
import json
import logging
import random
import threading
import time
import uuid
from datetime import datetime, timedelta
from collections import deque

import requests
from requests.exceptions import RequestException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('guardian-simulator')

# Default GPS coordinates (can be overridden in device config)
# These cover a range of points that could be in a forest area
DEFAULT_COORDINATES = [
    {"latitude": 37.7749, "longitude": -122.4194},  # San Francisco
    {"latitude": 37.8651, "longitude": -119.5383},  # Yosemite
    {"latitude": 36.4864, "longitude": -118.5658},  # Sequoia
    {"latitude": 40.3428, "longitude": -121.4092},  # Lassen
    {"latitude": 38.8876, "longitude": -120.0777},  # Tahoe
]

class GuardianDevice:
    """Simulates a Guardian forest monitoring device."""
    
    def __init__(self, device_id, config):
        """Initialize a simulated Guardian device.
        
        Args:
            device_id (int): Identifier for this device
            config (dict): Configuration parameters
        """
        self.device_id = device_id
        self.config = config
        self.code_name = f"GUARDIAN-{device_id:03d}"
        self.api_endpoint = config['endpoint']
        self.api_key = config['api_key']
        self.transmission_interval = config['interval']
        self.alert_probability = config['alert_probability']
        self.verbose = config['verbose']
        
        # Choose a location for this device
        location_idx = device_id % len(DEFAULT_COORDINATES)
        base_location = DEFAULT_COORDINATES[location_idx]
        # Add small random offset to avoid all devices at exact same position
        random_offset = random.uniform(-0.01, 0.01)
        self.gps_coordinates = {
            "latitude": base_location["latitude"] + random_offset,
            "longitude": base_location["longitude"] + random_offset
        }
        
        # Initialize sensor history to track trends
        self.temperature_history = deque(maxlen=12)  # Last 12 readings
        self.humidity_history = deque(maxlen=12)
        self.smoke_history = deque(maxlen=12)
        
        # Initialize baseline values (normal conditions)
        self.baseline_temperature = random.uniform(18, 25)  # 18-25°C
        self.baseline_humidity = random.uniform(50, 70)     # 50-70%
        self.baseline_smoke = random.uniform(50, 150)       # Low smoke level
        
        # Set initial battery level between 70-100%
        self.battery_percentage = random.uniform(70, 100)
        self.charging = random.random() > 0.7  # 30% chance of being in charging state
        
        # Initialize device state
        self.status = "ACTIVE"
        self.uptime_hours = 0
        self.last_transmission = None
        self.anomaly_active = False
        self.anomaly_type = None
        self.anomaly_duration = 0
        self.anomaly_start_time = None
        
        # Detection state
        self.fire_detected = False
        self.logging_detected = False
        self.detection_time = None
        self.detection_confidence = 0.0
        self.detection_type = None
        
        logger.info(f"Initialized {self.code_name} at {self.gps_coordinates}")
    
    def start(self):
        """Start the device simulation in a separate thread."""
        self.running = True
        self.thread = threading.Thread(target=self._run_simulation)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"{self.code_name} started simulation")
    
    def stop(self):
        """Stop the device simulation."""
        self.running = False
        logger.info(f"{self.code_name} stopped")
    
    def _run_simulation(self):
        """Main simulation loop for the device."""
        # Initial delay to stagger device transmissions
        initial_delay = random.uniform(1, 10)
        time.sleep(initial_delay)
        
        # First transmission to register device
        self._generate_and_transmit_data()
        
        while self.running:
            # Wait for the configured interval
            time.sleep(self.transmission_interval)
            
            # Update device state
            self._update_device_state()
            
            # Possibly create an anomaly
            self._maybe_create_anomaly()
            
            # Generate and transmit sensor data
            self._generate_and_transmit_data()
    
    def _update_device_state(self):
        """Update the internal state of the device."""
        # Update uptime
        self.uptime_hours += self.transmission_interval / 3600
        
        # Update battery
        if self.charging:
            # Battery increases when charging (slower as it gets fuller)
            self.battery_percentage += random.uniform(0.1, 0.5) * (100 - self.battery_percentage) / 100
            if self.battery_percentage > 99:
                self.battery_percentage = 100
                # 10% chance to stop charging when full
                if random.random() < 0.1:
                    self.charging = False
        else:
            # Battery decreases when not charging
            self.battery_percentage -= random.uniform(0.05, 0.2)
            if self.battery_percentage < 15:
                # Higher chance to start charging when low
                if random.random() < 0.3:
                    self.charging = True
        
        # Ensure battery stays in valid range
        self.battery_percentage = max(5, min(100, self.battery_percentage))
        
        # Random chance of status change
        if random.random() < 0.01:  # 1% chance of status change
            self.status = random.choice(["ACTIVE", "MAINTENANCE", "DEGRADED"])
    
    def _maybe_create_anomaly(self):
        """Possibly create an environmental anomaly (fire or logging)."""
        # If no anomaly is active, maybe start one
        if not self.anomaly_active and random.random() < self.alert_probability:
            self.anomaly_active = True
            self.anomaly_type = random.choice(["FIRE", "LOGGING"])
            self.anomaly_duration = random.randint(2, 5)  # Last for 2-5 transmission cycles
            self.anomaly_start_time = datetime.utcnow()
            
            if self.verbose:
                logger.info(f"{self.code_name} starting {self.anomaly_type} anomaly for {self.anomaly_duration} cycles")
        
        # If anomaly is active, check if it should end
        elif self.anomaly_active:
            anomaly_elapsed = (datetime.utcnow() - self.anomaly_start_time).total_seconds() / self.transmission_interval
            if anomaly_elapsed >= self.anomaly_duration:
                if self.verbose:
                    logger.info(f"{self.code_name} ending {self.anomaly_type} anomaly")
                self.anomaly_active = False
                self.anomaly_type = None
                self.fire_detected = False
                self.logging_detected = False
                self.detection_time = None
    
    def _generate_sensor_data(self):
        """Generate simulated sensor readings."""
        # Base environmental values with random fluctuation
        temperature = self.baseline_temperature + random.uniform(-1, 1)
        humidity = self.baseline_humidity + random.uniform(-5, 5)
        smoke_level = self.baseline_smoke + random.uniform(-20, 20)
        
        # Apply time-of-day effect (warmer in day, cooler at night)
        hour = datetime.utcnow().hour
        time_factor = abs(hour - 12) / 12  # 0 at noon, 1 at midnight
        temperature -= time_factor * random.uniform(3, 6)
        humidity += time_factor * random.uniform(5, 15)
        
        # Apply seasonal effects (simple simulation)
        day_of_year = datetime.utcnow().timetuple().tm_yday
        seasonal_factor = abs((day_of_year - 183) / 183)  # 0 at middle of year, 1 at start/end
        temperature -= seasonal_factor * random.uniform(2, 8)
        humidity += seasonal_factor * random.uniform(10, 20)
        
        # Apply anomaly effects if active
        if self.anomaly_active:
            if self.anomaly_type == "FIRE":
                # Fire causes increased temperature, decreased humidity, increased smoke
                temperature += random.uniform(15, 30)
                humidity -= random.uniform(20, 40)
                smoke_level += random.uniform(400, 800)
                
                # Set detection state
                self.fire_detected = True
                self.logging_detected = False
                self.detection_time = datetime.utcnow().isoformat() + "Z"
                self.detection_confidence = random.uniform(0.75, 0.98)
                self.detection_type = "fire"
                
            elif self.anomaly_type == "LOGGING":
                # Logging doesn't significantly affect environmental readings,
                # but we'll add small changes to simulate dust
                temperature += random.uniform(0, 2)
                humidity -= random.uniform(0, 5)
                smoke_level += random.uniform(50, 150)
                
                # Set detection state
                self.fire_detected = False
                self.logging_detected = True
                self.detection_time = datetime.utcnow().isoformat() + "Z"
                self.detection_confidence = random.uniform(0.75, 0.98)
                self.detection_type = random.choice(["chainsaw", "vehicle", "machinery"])
        
        # Ensure values are in realistic ranges
        temperature = max(0, min(50, temperature))
        humidity = max(10, min(100, humidity))
        smoke_level = max(0, min(1000, smoke_level))
        
        # Add to history
        self.temperature_history.append(temperature)
        self.humidity_history.append(humidity)
        self.smoke_history.append(smoke_level)
        
        return temperature, humidity, smoke_level
    
    def _generate_device_payload(self, temperature, humidity, smoke_level):
        """Generate the full device payload in the expected format."""
        now = datetime.utcnow()
        timestamp = now.isoformat() + "Z"  # ISO format with Z for UTC
        
        # Calculate estimated runtime based on battery level
        if self.charging:
            estimated_runtime = 24 * 7  # 1 week when charging
        else:
            # Roughly 4-5 days on full battery
            estimated_runtime = self.battery_percentage / 100 * 24 * 5
        
        # Build the payload
        payload = {
            "device_info": {
                "code_name": self.code_name,
                "timestamp": timestamp,
                "gps_coordinates": self.gps_coordinates,
                "battery": {
                    "percentage": round(self.battery_percentage, 1),
                    "charging": self.charging,
                    "estimated_runtime_hours": round(estimated_runtime, 1)
                },
                "status": self.status
            },
            "environment": {
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
                "smoke_level": round(smoke_level, 0),
                "last_reading_time": timestamp
            },
            "detections": {
                "fire": {
                    "detected": self.fire_detected,
                    "confidence": round(self.detection_confidence, 2) if self.fire_detected else 0.0,
                    "time_detected": self.detection_time if self.fire_detected else None
                },
                "logging": {
                    "detected": self.logging_detected,
                    "confidence": round(self.detection_confidence, 2) if self.logging_detected else 0.0,
                    "time_detected": self.detection_time if self.logging_detected else None,
                    "detection_type": self.detection_type if self.logging_detected else None
                }
            }
        }
        
        return payload
    
    def _generate_and_transmit_data(self):
        """Generate sensor data and transmit to the backend."""
        # Generate simulated sensor readings
        temperature, humidity, smoke_level = self._generate_sensor_data()
        
        # Create the full payload
        payload = self._generate_device_payload(temperature, humidity, smoke_level)
        
        # Send to backend
        self._transmit_data(payload)
        
        # Update last transmission time
        self.last_transmission = datetime.utcnow()
    
    def _transmit_data(self, payload):
        """Send data to the backend API."""
        headers = {
            'Content-Type': 'application/json',
            'X-Guardian-API-Key': self.api_key
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code in (200, 201, 202):
                if self.verbose or self.fire_detected or self.logging_detected:
                    alert_type = "FIRE ALERT" if self.fire_detected else "LOGGING ALERT" if self.logging_detected else "update"
                    logger.info(f"{self.code_name} sent {alert_type} - Status: {response.status_code}")
            else:
                logger.warning(f"{self.code_name} transmission failed - Status: {response.status_code}")
                logger.warning(f"Response: {response.text[:100]}...")
                
        except RequestException as e:
            logger.error(f"{self.code_name} transmission error: {e}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Guardian Sensor Network Simulator')
    parser.add_argument('--devices', type=int, default=3,
                      help='Number of Guardian devices to simulate (default: 3)')
    parser.add_argument('--interval', type=int, default=60,
                      help='Seconds between regular transmissions (default: 60)')
    parser.add_argument('--endpoint', type=str, 
                      default='http://localhost:5000/api/sensors/data',
                      help='Backend API endpoint URL')
    parser.add_argument('--api-key', type=str, default='demo-key-123',
                      help='API key for authentication')
    parser.add_argument('--alert-probability', type=float, default=0.1,
                      help='Probability of generating an alert (0-1)')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    
    return parser.parse_args()


def main():
    """Main function to run the Guardian simulator."""
    args = parse_arguments()
    
    # Validate arguments
    if args.devices < 1:
        logger.error("Number of devices must be at least 1")
        return
    
    if args.interval < 5:
        logger.error("Interval must be at least 5 seconds")
        return
    
    if args.alert_probability < 0 or args.alert_probability > 1:
        logger.error("Alert probability must be between 0 and 1")
        return
    
    logger.info(f"Starting Guardian Simulator with {args.devices} devices")
    logger.info(f"Sending data to {args.endpoint} every {args.interval} seconds")
    
    # Create device configuration
    config = {
        'endpoint': args.endpoint,
        'api_key': args.api_key,
        'interval': args.interval,
        'alert_probability': args.alert_probability,
        'verbose': args.verbose
    }
    
    # Create and start devices
    devices = []
    for i in range(args.devices):
        device = GuardianDevice(i+1, config)
        device.start()
        devices.append(device)
        # Small delay between starting devices to stagger transmissions
        time.sleep(1)
    
    logger.info(f"All {args.devices} Guardian devices are running")
    
    try:
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
        # Stop all devices
        for device in devices:
            device.stop()
        logger.info("Simulator stopped")


if __name__ == "__main__":
    main()
