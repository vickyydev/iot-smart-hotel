# iaq_sensor.py

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
API_URL = f"http://web:8000/api/rooms/{ROOM_ID}/data/iaq/"
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqtt')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = f"hotel/room/{ROOM_ID}/iaq"

def simulate_iaq_sensor():
    """Simulate IAQ sensor data."""
    while True:
        # Simulate sensor data
        temperature = round(random.uniform(18.0, 26.0), 2)
        humidity = round(random.uniform(30.0, 70.0), 2)
        co2 = round(random.uniform(400.0, 1000.0), 2)
        tvoc = round(random.uniform(0.0, 1.0), 2)
        pm25 = round(random.uniform(0.0, 100.0), 2)
        noise = round(random.uniform(30.0, 60.0), 2)
        illuminance = round(random.uniform(100.0, 1000.0), 2)
        online_status = True
        device_status = 'operational'

        data = {
            'room': ROOM_ID,
            'temperature': temperature,
            'humidity': humidity,
            'co2': co2,
            'tvoc': tvoc,
            'pm25': pm25,
            'noise': noise,
            'illuminance': illuminance,
            'online_status': online_status,
            'device_status': device_status
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
            logging.info(f"Published to MQTT topic {MQTT_TOPIC}")
        except Exception as e:
            logging.error(f"Error publishing to MQTT: {e}")

        # Sleep for 15 seconds
        time.sleep(15)

if __name__ == '__main__':
    simulate_iaq_sensor()
