from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import json
import base64
from .chat_interface import ChatInterface

chat_interface = ChatInterface()

@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def chat_home(request):
    """Render main chat interface"""
    return render(request, 'hotel/chat/index.html', {
        'initial_message': 'Welcome to Smart Hotel Assistant! How can I help you today?'
    })

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def chat_message(request):
    """Handle incoming chat messages"""
    try:
        data = json.loads(request.body)
        message_type = data.get('type', 'text')
        room_context = data.get('context', {})

        if message_type == 'text':
            response = chat_interface.process_text(data['message'], room_context)
        elif message_type == 'voice':
            audio_data = base64.b64decode(data['audio'].split(',')[1])
            response = chat_interface.process_voice_to_text(audio_data)
        elif message_type == 'image':
            response = chat_interface.process_image(
                data['image'],
                data.get('query')
            )
        else:
            response = "Unsupported message type"

        return JsonResponse({
            'response': response,
            'type': message_type
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def clear_chat(request):
    """Clear chat history"""
    chat_interface.clear_history()
    return JsonResponse({'status': 'success'})

@api_view(['GET'])
@permission_classes([AllowAny])
def list_deployments(request):
    """List available deployments for debugging"""
    deployments = chat_interface.list_deployments()
    return JsonResponse({'deployments': deployments})


@api_view(['GET'])
@permission_classes([AllowAny])
def check_azure_connection(request):
    """Check Azure OpenAI connection"""
    try:
        # Try a simple completion to test the connection
        response = chat_interface.process_text("Hello")
        return JsonResponse({
            'status': 'success',
            'response': response
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        })