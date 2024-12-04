# models.py

from django.apps import apps
from django.db import models
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils import timezone

# Ensure app is properly configured
if not apps.is_installed('hotel'):
    raise ImproperlyConfigured("Hotel app is not in INSTALLED_APPS")

class DeviceStatus(models.TextChoices):
    ON = 'ON', 'On'
    OFF = 'OFF', 'Off'
    ERROR = 'ERROR', 'Error'
    MAINTENANCE = 'MAINTENANCE', 'Maintenance'

class ACMode(models.TextChoices):
    COOL = 'COOL', 'Cooling'
    HEAT = 'HEAT', 'Heating'
    FAN = 'FAN', 'Fan Only'
    AUTO = 'AUTO', 'Automatic'
    OFF = 'OFF', 'Off'

class Hotel(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Floor(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='floors')
    number = models.IntegerField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['hotel', 'number']
        ordering = ['number']

    def __str__(self):
        return f"Floor {self.number} - {self.hotel.name}"

class Room(models.Model):
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    number = models.CharField(max_length=10)
    is_occupied = models.BooleanField(default=False)
    last_cleaned = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['floor', 'number']
        ordering = ['number']

    def __str__(self):
        return f"Room {self.number} - Floor {self.floor.number}"

# models.py

class RoomDevice(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='devices')
    device_type = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    settings = models.JSONField(default=dict)
    last_maintained = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['room', 'device_type']

    def __str__(self):
        return f"{self.device_type} - Room {self.room.number}"

class ACControl(models.Model):
    device = models.OneToOneField(RoomDevice, on_delete=models.CASCADE, related_name='ac_control')
    temperature = models.FloatField(default=24.0)
    mode = models.CharField(
        max_length=20,
        choices=ACMode.choices,
        default=ACMode.OFF
    )
    fan_speed = models.IntegerField(default=1)  # 1-5
    humidity_control = models.BooleanField(default=False)
    target_humidity = models.IntegerField(default=50)  # percentage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate the model"""
        errors = {}
        
        if self.temperature is not None:
            if self.temperature < 16 or self.temperature > 30:
                errors['temperature'] = 'Temperature must be between 16°C and 30°C'

        if self.fan_speed is not None:
            if self.fan_speed < 1 or self.fan_speed > 5:
                errors['fan_speed'] = 'Fan speed must be between 1 and 5'

        if self.target_humidity is not None:
            if self.target_humidity < 30 or self.target_humidity > 70:
                errors['target_humidity'] = 'Target humidity must be between 30% and 70%'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"AC Control - Room {self.device.room.number}"

class LightingControl(models.Model):
    device = models.OneToOneField(RoomDevice, on_delete=models.CASCADE, related_name='lighting_control')
    brightness = models.IntegerField(default=100)  # 0-100
    color_temperature = models.IntegerField(default=2700)  # Kelvin
    motion_sensor_enabled = models.BooleanField(default=True)
    auto_dim_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate the model"""
        errors = {}
        
        if self.brightness is not None:
            if self.brightness < 0 or self.brightness > 100:
                errors['brightness'] = 'Brightness must be between 0 and 100'

        if self.color_temperature is not None:
            if self.color_temperature < 2000 or self.color_temperature > 6500:
                errors['color_temperature'] = 'Color temperature must be between 2000K and 6500K'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Lighting Control - Room {self.device.room.number}"

class DeviceAutomation(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE, related_name='automation')
    ac_auto_adjust = models.BooleanField(default=True)
    lighting_auto_adjust = models.BooleanField(default=True)
    presence_timeout = models.IntegerField(default=15)  # minutes
    comfort_temperature = models.FloatField(default=24.0)
    energy_saving_temperature = models.FloatField(default=26.0)
    last_presence_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Automation Settings - Room {self.room.number}"

class EnergyConsumption(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='energy_consumption')
    device = models.ForeignKey(RoomDevice, on_delete=models.CASCADE, related_name='energy_readings')
    timestamp = models.DateTimeField(auto_now_add=True)
    power_usage = models.FloatField()  # in watts
    duration = models.IntegerField()  # in minutes
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # in local currency

    @property
    def energy_consumed(self):
        """Calculate energy consumption in kWh"""
        return (self.power_usage * self.duration) / (60 * 1000)

    def __str__(self):
        return f"Energy Consumption - {self.device.device_type} - Room {self.room.number}"

class IAQSensorData(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='iaq_data')
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    co2 = models.FloatField(null=True, blank=True)
    tvoc = models.FloatField(null=True, blank=True)
    pm25 = models.FloatField(null=True, blank=True)
    noise = models.FloatField(null=True, blank=True)
    illuminance = models.FloatField(null=True, blank=True)
    online_status = models.BooleanField(default=True)
    device_status = models.CharField(max_length=20, default='operational')

    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"IAQ Data - Room {self.room.number} - {self.timestamp}"

class LifeBeingSensorData(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='life_being_data')
    timestamp = models.DateTimeField(auto_now_add=True)
    presence_detected = models.BooleanField(default=False)
    motion_level = models.IntegerField(default=0)  # 0-100
    presence_state = models.CharField(max_length=20, null=True, blank=True)
    sensitivity = models.FloatField(null=True, blank=True)
    online_status = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Life Being Data - Room {self.room.number} - {self.timestamp}"
