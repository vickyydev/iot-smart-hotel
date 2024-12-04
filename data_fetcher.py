# data_fetcher.py

import requests
import time
import json
import paho.mqtt.publish as publish
import os

MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqtt')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
ROOM_ID = os.getenv('ROOM_ID', '1')

SENSOR_URLS = {
    'iaq': f'http://iaq_sensor_room{ROOM_ID}:5000/sensor/data',
    'life_being': f'http://life_being_sensor_room{ROOM_ID}:5001/sensor/data',
}

def fetch_sensor_data():
    while True:
        for sensor_type, url in SENSOR_URLS.items():
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    topic = f"hotel/room/{ROOM_ID}/{sensor_type}"
                    publish.single(
                        topic=topic,
                        payload=json.dumps(data),
                        hostname=MQTT_BROKER,
                        port=MQTT_PORT
                    )
                    print(f"Published data to topic {topic}")
                else:
                    print(f"No data from {sensor_type}")
            except Exception as e:
                print(f"Error fetching data from {sensor_type}: {e}")
        time.sleep(5)

if __name__ == '__main__':
    fetch_sensor_data()
