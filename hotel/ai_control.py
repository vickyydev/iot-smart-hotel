# ai_control.py

class RoomAIController:
    def __init__(self, room):
        self.room = room

    def optimize_environment(self):
        """Optimize room environment based on sensor data and preferences"""
        latest_iaq = self.room.iaq_data.order_by('-timestamp').first()
        latest_presence = self.room.life_being_data.order_by('-timestamp').first()

        ac_device = self.room.devices.filter(device_type='AC').first()
        if not ac_device:
            return

        ac_control = ac_device.ac_control

        if latest_presence and latest_presence.presence_detected:
            # Guest is present
            desired_temp = 22.0  # Comfort temperature
            if latest_iaq and latest_iaq.temperature:
                if latest_iaq.temperature > desired_temp:
                    ac_control.mode = 'COOL'
                    ac_control.temperature = desired_temp
                elif latest_iaq.temperature < desired_temp:
                    ac_control.mode = 'HEAT'
                    ac_control.temperature = desired_temp
                else:
                    ac_control.mode = 'FAN'
            else:
                ac_control.mode = 'AUTO'
            ac_control.save()
        else:
            # Guest is not present
            ac_control.mode = 'OFF'
            ac_control.save()
