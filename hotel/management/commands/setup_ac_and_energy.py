# hotel/management/commands/setup_ac_and_energy.py

from django.core.management.base import BaseCommand
from hotel.models import Room, RoomDevice, ACControl, DeviceStatus, EnergyConsumption
from django.utils import timezone
from datetime import timedelta
from random import uniform

class Command(BaseCommand):
    help = 'Add AC devices to all rooms without one and generate sample energy data'

    def handle(self, *args, **options):
        self.add_ac_devices()
        self.create_sample_energy_data()
        self.stdout.write(self.style.SUCCESS('AC devices added and sample energy data generated.'))

    def add_ac_devices(self):
        rooms = Room.objects.all()
        for room in rooms:
            if not room.devices.filter(device_type='AC').exists():
                device = RoomDevice.objects.create(
                    room=room,
                    device_type='AC',
                    name=f'AC Unit - Room {room.number}',
                    status=DeviceStatus.OFF,
                    settings={'initial_temp': 24.0, 'mode': 'OFF'}
                )
                ACControl.objects.create(device=device)
                self.stdout.write(self.style.SUCCESS(f'Added AC device to room {room.number}'))
            else:
                self.stdout.write(f'Room {room.number} already has an AC device')

    def create_sample_energy_data(self):
        rooms = Room.objects.all()
        for room in rooms:
            devices = room.devices.all()
            for device in devices:
                for day in range(7):
                    timestamp = timezone.now() - timedelta(days=day)
                    power_usage = uniform(100, 500)  # Random power usage between 100W and 500W
                    duration = 60  # Duration in minutes
                    EnergyConsumption.objects.create(
                        room=room,
                        device=device,
                        timestamp=timestamp,
                        power_usage=power_usage,
                        duration=duration,
                        cost=(power_usage * duration / 1000) * 0.1  # Cost calculation
                    )
        self.stdout.write(self.style.SUCCESS('Sample energy data created for all devices in all rooms.'))
