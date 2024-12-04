from rest_framework import serializers
from .models import (
    Hotel,
    Floor,
    Room,
    RoomDevice,
    ACControl,
    LightingControl,
    DeviceAutomation,
    EnergyConsumption,
    IAQSensorData,
    LifeBeingSensorData
)

class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = ['id', 'name', 'address', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'hotel', 'number', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_number(self, value):
        """
        Check that the floor number is positive
        """
        if value < 0:
            raise serializers.ValidationError("Floor number must be positive")
        return value

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = [
            'id', 'floor', 'number', 'is_occupied',
            'last_cleaned', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ACControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = ACControl
        fields = [
            'id', 'device', 'temperature', 'mode',
            'fan_speed', 'humidity_control', 'target_humidity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_temperature(self, value):
        """
        Check that the temperature is within reasonable bounds
        """
        if value < 16 or value > 30:
            raise serializers.ValidationError(
                "Temperature must be between 16°C and 30°C"
            )
        return value

    def validate_fan_speed(self, value):
        """
        Check that fan speed is between 1 and 5
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError("Fan speed must be between 1 and 5")
        return value

class LightingControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = LightingControl
        fields = [
            'id', 'device', 'brightness', 'color_temperature',
            'motion_sensor_enabled', 'auto_dim_enabled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_brightness(self, value):
        """
        Check that brightness is between 0 and 100
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Brightness must be between 0 and 100"
            )
        return value

    def validate_color_temperature(self, value):
        """
        Check that color temperature is within reasonable bounds
        """
        if value < 2000 or value > 6500:
            raise serializers.ValidationError(
                "Color temperature must be between 2000K and 6500K"
            )
        return value

class RoomDeviceSerializer(serializers.ModelSerializer):
    ac_control = ACControlSerializer(read_only=True)
    lighting_control = LightingControlSerializer(read_only=True)
    settings = serializers.JSONField()

    class Meta:
        model = RoomDevice
        fields = [
            'id', 'room', 'name', 'device_type', 'status',
            'settings', 'last_maintained', 'last_updated', 'created_at',
            'ac_control', 'lighting_control'
        ]
        read_only_fields = ['created_at', 'last_updated']

    def create(self, validated_data):
        settings = validated_data.get('settings', {})
        device = super().create(validated_data)
        
        if device.device_type == 'AC':
            ACControl.objects.create(
                device=device,
                temperature=settings.get('temperature', 24.0),
                mode=settings.get('mode', 'AUTO'),
                fan_speed=settings.get('fan_speed', 1),
                humidity_control=True,
                target_humidity=50
            )
        return device

class DeviceAutomationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceAutomation
        fields = [
            'id', 'room', 'ac_auto_adjust', 'lighting_auto_adjust',
            'presence_timeout', 'comfort_temperature',
            'energy_saving_temperature', 'last_presence_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_presence_time']

    def validate_presence_timeout(self, value):
        """
        Check that presence timeout is reasonable
        """
        if value < 1 or value > 60:
            raise serializers.ValidationError(
                "Presence timeout must be between 1 and 60 minutes"
            )
        return value

class EnergyConsumptionSerializer(serializers.ModelSerializer):
    energy_consumed = serializers.FloatField(read_only=True)

    class Meta:
        model = EnergyConsumption
        fields = [
            'id', 'room', 'device', 'timestamp',
            'power_usage', 'duration', 'cost',
            'energy_consumed'
        ]
        read_only_fields = ['timestamp']

class IAQSensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = IAQSensorData
        fields = [
            'id', 'room', 'timestamp', 'temperature',
            'humidity', 'co2', 'tvoc', 'pm25', 'noise',
            'illuminance', 'online_status', 'device_status'
        ]
        read_only_fields = ['timestamp']

    def validate_co2(self, value):
        """
        Check that CO2 levels are within reasonable bounds
        """
        if value and (value < 0 or value > 5000):
            raise serializers.ValidationError(
                "CO2 levels must be between 0 and 5000 ppm"
            )
        return value

class LifeBeingSensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = LifeBeingSensorData
        fields = [
            'id', 'room', 'timestamp', 'presence_detected',
            'motion_level', 'presence_state', 'sensitivity',
            'online_status'
        ]
        read_only_fields = ['timestamp']

    def validate_motion_level(self, value):
        """
        Check that motion level is between 0 and 100
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Motion level must be between 0 and 100"
            )
        return value

# Nested Serializers for detailed views
class DetailedRoomSerializer(RoomSerializer):
    devices = RoomDeviceSerializer(many=True, read_only=True)
    automation = DeviceAutomationSerializer(read_only=True)
    energy_consumption = serializers.SerializerMethodField()
    iaq_data = serializers.SerializerMethodField()
    life_being_data = serializers.SerializerMethodField()

    class Meta(RoomSerializer.Meta):
        fields = RoomSerializer.Meta.fields + [
            'devices', 'automation', 'energy_consumption',
            'iaq_data', 'life_being_data'
        ]

    def get_energy_consumption(self, obj):
        """Get the latest energy consumption data"""
        latest = obj.energy_consumption.order_by('-timestamp').first()
        if latest:
            return EnergyConsumptionSerializer(latest).data
        return None

    def get_iaq_data(self, obj):
        """Get the latest IAQ sensor data"""
        latest = obj.iaq_data.order_by('-timestamp').first()
        if latest:
            return IAQSensorDataSerializer(latest).data
        return None

    def get_life_being_data(self, obj):
        """Get the latest life being sensor data"""
        latest = obj.life_being_data.order_by('-timestamp').first()
        if latest:
            return LifeBeingSensorDataSerializer(latest).data
        return None

class DetailedFloorSerializer(FloorSerializer):
    rooms = DetailedRoomSerializer(many=True, read_only=True)

    class Meta(FloorSerializer.Meta):
        fields = FloorSerializer.Meta.fields + ['rooms']

class DetailedHotelSerializer(HotelSerializer):
    floors = DetailedFloorSerializer(many=True, read_only=True)

    class Meta(HotelSerializer.Meta):
        fields = HotelSerializer.Meta.fields + ['floors']