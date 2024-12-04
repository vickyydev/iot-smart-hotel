from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from hotel.views import HomeView

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "healthy"}, status=200)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('chat/', include('hotel.chat.urls')),
    path('api/', include('hotel.urls')),  # All API URLs should be under this
    path('health/', health_check, name='health_check'),
]