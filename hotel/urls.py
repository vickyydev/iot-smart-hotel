from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from . import views

# Main router
router = DefaultRouter()
router.register(r'hotels', views.HotelViewSet, basename='hotel')

# Hotel -> Floor -> Room hierarchy
hotel_router = NestedDefaultRouter(router, r'hotels', lookup='hotel')  # Changed this line
hotel_router.register(r'floors', views.FloorViewSet, basename='hotel-floors')

floor_router = NestedDefaultRouter(hotel_router, r'floors', lookup='floor')  # Changed this line
floor_router.register(r'rooms', views.RoomViewSet, basename='floor-rooms')

room_router = NestedDefaultRouter(floor_router, r'rooms', lookup='room')  # Changed this line
room_router.register(r'devices', views.DeviceControlViewSet, basename='room-devices')
room_router.register(r'automation', views.AutomationViewSet, basename='room-automation')

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health-check'),

    # Room access by number endpoints
    path('rooms/by-number/<str:number>/status/', 
         views.RoomViewSet.as_view({'get': 'get_status_by_number'}),
         name='room-status-by-number'),
         
    path('rooms/by-number/<str:number>/energy-report/', 
         views.RoomViewSet.as_view({'get': 'get_energy_report_by_number'}),
         name='room-energy-report-by-number'),

    # Sensor data endpoints with room number
    path('rooms/by-number/<str:number>/data/iaq/',
         views.IAQSensorDataViewSet.as_view({
             'get': 'list_by_number',
             'post': 'create_by_number'
         }),
         name='room-iaq-data-by-number'),

    path('rooms/by-number/<str:number>/data/life-being/',
         views.LifeBeingSensorDataViewSet.as_view({
             'get': 'list_by_number',
             'post': 'create_by_number'
         }),
         name='room-life-being-data-by-number'),

    # Device control by room number
     path('rooms/by-number/<str:number>/ac/control/', 
          views.DeviceControlViewSet.as_view({'post': 'control_ac_by_room_number'}),
          name='ac-control-by-room-number'),

    # Energy endpoints
    path('energy/summary/',
         views.EnergyConsumptionViewSet.as_view({'get': 'summary'}),
         name='energy-summary'),

    # Legacy endpoints (keeping for backward compatibility)
    path('rooms/<int:pk>/status/', 
         views.RoomViewSet.as_view({'get': 'status'}),
         name='room-status'),
         
    path('rooms/<int:pk>/energy-report/', 
         views.RoomViewSet.as_view({'get': 'energy_report'}),
         name='room-energy-report'),

    path('rooms/<int:room_id>/data/iaq/',
         views.IAQSensorDataViewSet.as_view({
             'get': 'list',
             'post': 'create'
         }),
         name='room-iaq-data'),

    path('rooms/<int:room_id>/data/life-being/',
         views.LifeBeingSensorDataViewSet.as_view({
             'get': 'list',
             'post': 'create'
         }),
         name='room-life-being-data'),

     path('rooms/<int:room_id>/devices/<int:pk>/control/', 
         views.DeviceControlViewSet.as_view({'post': 'control'}),
         name='device-control'),

    # Include router URLs
    path('', include(router.urls)),
    path('', include(hotel_router.urls)),
    path('', include(floor_router.urls)),
    path('', include(room_router.urls)),
]