# life_being_sensor.py

import requests
import time
import json
import random
import os
import logging
import paho.mqtt.publish as mqtt_publish

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables
ROOM_ID = os.getenv('ROOM_ID', '1')
API_URL = f"http://web:8000/api/rooms/{ROOM_ID}/data/life-being/"
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqtt')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = f"hotel/room/{ROOM_ID}/life_being"

def simulate_life_being_sensor():
    """Simulate life being sensor data."""
    while True:
        # Simulate sensor data
        presence_detected = random.choice([True, False])
        motion_level = random.randint(0, 100) if presence_detected else 0
        presence_state = 'occupied' if presence_detected else 'unoccupied'
        sensitivity = round(random.uniform(0.5, 1.0), 2)
        online_status = True

        data = {
            'room': ROOM_ID,
            'presence_detected': presence_detected,
            'motion_level': motion_level,
            'presence_state': presence_state,
            'sensitivity': sensitivity,
            'online_status': online_status
        }

        # Send data to API
        try:
            logging.info(f"Sending data to {API_URL}")
            logging.info(f"Data: {data}")

            response = requests.post(API_URL, json=data)

            if response.status_code == 201:
                logging.info(f"Response status: {response.status_code}")
                logging.info(f"Response content: {response.json()}")
                logging.info("Successfully sent data to API")
            else:
                logging.error(f"Failed to send data. Status: {response.status_code}")
                logging.error(f"Response: {response.text}")

        except Exception as e:
            logging.error(f"Error sending data to API: {e}")

        # Publish to MQTT
        try:
            mqtt_publish.single(
                topic=MQTT_TOPIC,
                payload=json.dumps(data),
                hostname=MQTT_BROKER,
                port=MQTT_PORT
            )
            logging.info(f"Published to MQTT topic {MQTT_TOPIC}: {data}")
        except Exception as e:
            logging.error(f"Error publishing to MQTT: {e}")

        # Sleep for 15 seconds to reduce frequency and avoid rate limiting
        time.sleep(15)

if __name__ == '__main__':
    simulate_life_being_sensor()
