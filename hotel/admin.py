from django.contrib import admin
from .models import Hotel, Floor, Room, LifeBeingSensorData, IAQSensorData

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'floor', 'number')  # Add 'id' here

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotel', 'number')

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(LifeBeingSensorData)
class LifeBeingSensorDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'online_status', 'sensitivity', 'presence_state', 'timestamp')

@admin.register(IAQSensorData)
class IAQSensorDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'noise', 'co2', 'pm25', 'humidity', 'temperature', 'illuminance', 'online_status', 'device_status', 'timestamp')
