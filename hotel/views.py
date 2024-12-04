from pydantic import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Sum, Count
from datetime import timedelta
import logging
from django.views.generic import TemplateView

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
    LifeBeingSensorData,
    DeviceStatus,
    ACMode
)

from .serializers import (
    HotelSerializer,
    FloorSerializer,
    RoomSerializer,
    DetailedHotelSerializer,
    DetailedFloorSerializer,
    DetailedRoomSerializer,
    RoomDeviceSerializer,
    ACControlSerializer,
    LightingControlSerializer,
    DeviceAutomationSerializer,
    EnergyConsumptionSerializer,
    IAQSensorDataSerializer,
    LifeBeingSensorDataSerializer
)

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """System health check endpoint"""
    try:
        Room.objects.first()
        return Response(
            {"status": "healthy", "timestamp": timezone.now()},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response(
            {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": timezone.now()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedHotelSerializer
        return HotelSerializer

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        hotel = self.get_object()
        rooms = Room.objects.filter(floor__hotel=hotel)

        return Response({
            'total_rooms': rooms.count(),
            'occupied_rooms': rooms.filter(is_occupied=True).count(),
            'total_floors': hotel.floors.count(),
            'average_energy_consumption': EnergyConsumption.objects.filter(
                room__floor__hotel=hotel
            ).aggregate(avg=Avg('power_usage'))['avg']
        })

class FloorViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        if 'hotel_pk' in self.kwargs:
            return Floor.objects.filter(hotel_id=self.kwargs['hotel_pk'])
        return Floor.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedFloorSerializer
        return FloorSerializer

    @action(detail=True, methods=['get'])
    def statistics(self, request, hotel_pk=None, pk=None):
        floor = self.get_object()
        rooms = floor.rooms.all()

        return Response({
            'total_rooms': rooms.count(),
            'occupied_rooms': rooms.filter(is_occupied=True).count(),
            'average_temperature': IAQSensorData.objects.filter(
                room__floor=floor
            ).aggregate(avg=Avg('temperature'))['avg']
        })

class RoomViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        if 'floor_pk' in self.kwargs:
            return Room.objects.filter(floor_id=self.kwargs['floor_pk'])
        return Room.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedRoomSerializer
        return RoomSerializer

    def _get_room_status_data(self, room):
        """Helper method to get room status data"""
        latest_iaq = room.iaq_data.order_by('-timestamp').first()
        latest_life = room.life_being_data.order_by('-timestamp').first()
        devices = room.devices.all()
        ac = devices.filter(device_type='AC').first()
        lighting = devices.filter(device_type='LIGHTING').first()

        return {
            'room_number': room.number,
            'occupied': room.is_occupied,
            'last_cleaned': room.last_cleaned,
            'environmental_data': IAQSensorDataSerializer(latest_iaq).data if latest_iaq else None,
            'presence_data': LifeBeingSensorDataSerializer(latest_life).data if latest_life else None,
            'ac_status': ACControlSerializer(ac.ac_control).data if ac and hasattr(ac, 'ac_control') else None,
            'lighting_status': LightingControlSerializer(lighting.lighting_control).data if lighting and hasattr(lighting, 'lighting_control') else None,
        }

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Legacy status endpoint using room ID"""
        room = self.get_object()
        return Response(self._get_room_status_data(room))

    @action(detail=False, methods=['get'], url_path='by-number/(?P<number>\w+)/status')
    def get_status_by_number(self, request, number=None):
        """Get room status by room number"""
        try:
            room = Room.objects.get(number=number)
            return Response(self._get_room_status_data(room))
        except Room.DoesNotExist:
            return Response(
                {"error": f"Room {number} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def _get_energy_report_data(self, room, days=1):
        """Helper method to get energy report data"""
        start_date = timezone.now() - timedelta(days=days)
        consumption = EnergyConsumption.objects.filter(
            room=room,
            timestamp__gte=start_date
        )

        return {
            'total_consumption': consumption.aggregate(Sum('power_usage'))['power_usage__sum'],
            'average_daily_consumption': consumption.values('device__device_type').annotate(
                avg_usage=Avg('power_usage'),
                total_usage=Sum('power_usage')
            ).order_by('device__device_type')
        }

    @action(detail=True, methods=['get'])
    def energy_report(self, request, pk=None):
        """Legacy energy report endpoint using room ID"""
        room = self.get_object()
        days = int(request.query_params.get('days', 1))
        return Response(self._get_energy_report_data(room, days))

    @action(detail=False, methods=['get'], url_path='by-number/(?P<number>\w+)/energy-report')
    def get_energy_report_by_number(self, request, number=None):
        """Get energy report by room number"""
        try:
            room = Room.objects.get(number=number)
            days = int(request.query_params.get('days', 1))
            return Response(self._get_energy_report_data(room, days))
        except Room.DoesNotExist:
            return Response(
                {"error": f"Room {number} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class DeviceControlViewSet(viewsets.ModelViewSet):
    serializer_class = RoomDeviceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if 'room_pk' in self.kwargs:
            return RoomDevice.objects.filter(room_id=self.kwargs['room_pk'])
        return RoomDevice.objects.all()

    def _process_device_control(self, room, device_id, request_data):
        """Helper method to process device control"""
        device = get_object_or_404(RoomDevice, id=device_id, room=room)

        if device.device_type == 'AC':
            ac_control, created = ACControl.objects.get_or_create(device=device)
            serializer = ACControlSerializer(ac_control, data=request_data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                device.status = DeviceStatus.ON if request_data.get('mode') != 'OFF' else DeviceStatus.OFF
                device.save()

                return Response({
                    "status": "success",
                    "message": "AC settings updated successfully",
                    "device_type": "AC",
                    "room_number": room.number,
                    "settings": serializer.data
                })
            return Response(
                {"error": "Invalid settings", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {"error": f"Device {device_id} is not an AC device."},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def control(self, request, pk=None, room_id=None):
        """Legacy device control endpoint using room ID"""
        try:
            room = get_object_or_404(Room, id=room_id)
            return self._process_device_control(room, pk, request.data)
        except Exception as e:
            logger.error(f"Device control error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='by-number/(?P<number>\w+)/control')
    def control_by_number(self, request, number=None, pk=None):
        """Control device by room number"""
        try:
            # Find the room
            room = Room.objects.get(number=number)
            
            # Find the device using pk (which is device_id)
            device = room.devices.get(id=pk)
            
            if device.device_type == 'AC':
                ac_control, created = ACControl.objects.get_or_create(device=device)
                serializer = ACControlSerializer(ac_control, data=request.data, partial=True)
                
                if serializer.is_valid():
                    serializer.save()
                    device.status = DeviceStatus.ON if request.data.get('mode') != 'OFF' else DeviceStatus.OFF
                    device.save()

                    return Response({
                        "status": "success",
                        "message": "AC settings updated successfully",
                        "device_type": "AC",
                        "room_number": room.number,
                        "settings": serializer.data
                    })
                return Response(
                    {"error": "Invalid settings", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {"error": f"Device {pk} is not an AC device."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Room.DoesNotExist:
            return Response(
                {"error": f"Room {number} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except RoomDevice.DoesNotExist:
            return Response(
                {"error": f"Device not found in room {number}. Available devices: {[d.id for d in room.devices.all()]}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Device control error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @action(detail=False, methods=['post'], url_path='by-number/(?P<number>\w+)/ac/control')
    def control_ac_by_room_number(self, request, number=None):
        try:
            room = Room.objects.get(number=number)
            device = room.devices.filter(device_type='AC').first()
            if not device:
                return Response(
                    {"error": f"No AC device found in room {number}"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Process AC control
            ac_control, created = ACControl.objects.get_or_create(device=device)
            serializer = ACControlSerializer(ac_control, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                device.status = DeviceStatus.ON if request.data.get('mode') != 'OFF' else DeviceStatus.OFF
                device.save()

                # Get the latest IAQ reading
                latest_iaq = room.iaq_data.order_by('-timestamp').first()
                if latest_iaq:
                    # Directly set the temperature without gradual change
                    target_temp = float(request.data.get('temperature', 24.0))
                    latest_iaq.temperature = target_temp
                    latest_iaq.save()

                return Response({
                    "status": "success",
                    "message": "AC settings updated successfully",
                    "device_type": "AC",
                    "room_number": room.number,
                    "settings": serializer.data
                })
            return Response(
                {"error": "Invalid settings", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Room.DoesNotExist:
            return Response(
                {"error": f"Room {number} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Device control error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class IAQSensorDataViewSet(viewsets.ModelViewSet):
    serializer_class = IAQSensorDataSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        room_id = self.kwargs.get('room_id')
        if room_id:
            return IAQSensorData.objects.filter(room_id=room_id)
        return IAQSensorData.objects.all()

    def list_by_number(self, request, number=None):
        """Get IAQ data by room number"""
        try:
            room = Room.objects.get(number=number)
            queryset = self.get_queryset().filter(room=room)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Room.DoesNotExist:
            return Response(
                {"error": f"Room {number} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def create_by_number(self, request, number=None):
        """Create IAQ data by room number"""
        try:
            room = Room.objects.get(number=number)
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save(room=room)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Room.DoesNotExist:
            return Response(
                {"error": f"Room {number} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class LifeBeingSensorDataViewSet(viewsets.ModelViewSet):
    serializer_class = LifeBeingSensorDataSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        room_id = self.kwargs.get('room_id')
        if room_id:
            return LifeBeingSensorData.objects.filter(room_id=room_id)
        return LifeBeingSensorData.objects.all()

    def list_by_number(self, request, number=None):
        """Get life being data by room number"""
        try:
            room = Room.objects.get(number=number)
            queryset = self.get_queryset().filter(room=room)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Room.DoesNotExist:
            return Response(
                {"error": f"Room {number} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def create_by_number(self, request, number=None):
        """Create life being data by room number"""
        try:
            room = Room.objects.get(number=number)
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save(room=room)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Room.DoesNotExist:
            return Response(
                {"error": f"Room {number} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class EnergyConsumptionViewSet(viewsets.ModelViewSet):
    serializer_class = EnergyConsumptionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        room_id = self.kwargs.get('room_pk')
        if room_id:
            return EnergyConsumption.objects.filter(room_id=room_id)
        return EnergyConsumption.objects.all()

    @action(detail=False, methods=['get'])
    def summary(self, request):
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        consumption = self.get_queryset().filter(timestamp__gte=start_date)

        return Response({
            'total_consumption': consumption.aggregate(Sum('power_usage'))['power_usage__sum'],
            'by_device_type': consumption.values('device__device_type').annotate(
                total_usage=Sum('power_usage'),
                average_usage=Avg('power_usage'),
                count=Count('id')
            ),
            'by_day': consumption.values('timestamp__date').annotate(
                total_usage=Sum('power_usage')
            ).order_by('timestamp__date')
        })

class HomeView(TemplateView):
    template_name = 'hotel/home.html'


class AutomationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for room automation settings.
    Supports automation configuration and control.
    """
    serializer_class = DeviceAutomationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if 'room_pk' in self.kwargs:
            return DeviceAutomation.objects.filter(room_id=self.kwargs['room_pk'])
        return DeviceAutomation.objects.all()

    @action(detail=True, methods=['post'])
    def apply_automation(self, request, pk=None):
        """Manually trigger automation for a room"""
        automation = self.get_object()
        room = automation.room

        try:
            # Get latest sensor data
            latest_presence = room.life_being_data.latest('timestamp')
            latest_iaq = room.iaq_data.latest('timestamp')

            # Apply automation logic
            if latest_presence.presence_detected:
                # Room is occupied
                if hasattr(room, 'devices'):
                    for device in room.devices.all():
                        if device.device_type == 'AC' and automation.ac_auto_adjust:
                            ac_control = device.ac_control
                            ac_control.temperature = automation.comfort_temperature
                            ac_control.save()
                        elif device.device_type == 'LIGHTING' and automation.lighting_auto_adjust:
                            lighting_control = device.lighting_control
                            if latest_iaq.illuminance < 300:
                                lighting_control.brightness = 100
                            else:
                                lighting_control.brightness = 50
                            lighting_control.save()

            return Response({"status": "Automation applied successfully"})

        except Exception as e:
            logger.error(f"Automation error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )