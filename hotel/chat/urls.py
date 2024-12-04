from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_home, name='chat-home'),
    path('api/message/', views.chat_message, name='chat-message'),
    path('api/clear/', views.clear_chat, name='chat-clear'),
    path('api/deployments/', views.list_deployments, name='list-deployments'),
    path('api/check-connection/', views.check_azure_connection, name='check-connection'),
]