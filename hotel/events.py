# events.py
import json
import paho.mqtt.client as mqtt
import logging
import threading
from django.conf import settings
from hotel.models import Room, IAQSensorData, LifeBeingSensorData
from django.db.models import ObjectDoesNotExist

logger = logging.getLogger(__name__)

class EventStream:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        try:
            self.client.connect(
                settings.MQTT_BROKER,
                settings.MQTT_PORT,
                60
            )
            self.thread = threading.Thread(target=self.client.loop_forever)
            self.thread.start()
            logger.info("MQTT client started")
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")

    def on_connect(self, client, userdata, flags, rc):
        """Subscribe to relevant topics on connect"""
        client.subscribe("hotel/room/+/iaq")
        client.subscribe("hotel/room/+/life_being")
        logger.info("Connected to MQTT broker and subscribed to topics")

    def on_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 4:
                logger.error(f"Invalid topic format: {msg.topic}")
                return

            room_id = topic_parts[2]
            sensor_type = topic_parts[3]

            data = json.loads(msg.payload.decode())
            logger.info(f"Received {sensor_type} data for room {room_id}")

            # Try to get the room, but don't raise error if it doesn't exist yet
            try:
                room = Room.objects.get(id=room_id)
                
                # Process data based on sensor type
                if sensor_type == 'iaq':
                    self.process_iaq_data(room, data)
                elif sensor_type == 'life_being':
                    self.process_life_being_data(room, data)
                else:
                    logger.warning(f"Unknown sensor type: {sensor_type}")

            except ObjectDoesNotExist:
                # Room doesn't exist yet - just log and continue
                logger.debug(f"Room {room_id} not found - skipping data processing")
                pass

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def process_iaq_data(self, room, data):
        """Process IAQ sensor data"""
        try:
            IAQSensorData.objects.create(
                room=room,
                temperature=data.get('temperature'),
                humidity=data.get('humidity'),
                co2=data.get('co2'),
                tvoc=data.get('tvoc'),
                pm25=data.get('pm25'),
                noise=data.get('noise'),
                illuminance=data.get('illuminance'),
                online_status=data.get('online_status', True),
                device_status=data.get('device_status', 'operational')
            )
            logger.info(f"IAQ data saved for room {room.id}")
        except Exception as e:
            logger.error(f"Error saving IAQ data: {e}")

    def process_life_being_data(self, room, data):
        """Process Life Being sensor data"""
        try:
            LifeBeingSensorData.objects.create(
                room=room,
                presence_detected=data.get('presence_detected', False),
                motion_level=data.get('motion_level', 0),
                presence_state=data.get('presence_state', 'unoccupied'),
                sensitivity=data.get('sensitivity', 0.5),
                online_status=data.get('online_status', True)
            )
            logger.info(f"Life Being data saved for room {room.id}")

            # Update room occupancy status
            self.update_room_occupancy(room, data)

        except Exception as e:
            logger.error(f"Error saving Life Being data: {e}")

    def update_room_occupancy(self, room, data):
        """Update room occupancy status"""
        try:
            is_occupied = data.get('presence_detected', False)
            if room.is_occupied != is_occupied:
                room.is_occupied = is_occupied
                room.save()
                logger.info(f"Updated room {room.id} occupancy to {is_occupied}")
        except Exception as e:
            logger.error(f"Error updating room occupancy: {e}")

if __name__ == '__main__':
    EventStream()