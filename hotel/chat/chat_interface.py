import json
import os
import time
import requests
import logging
from openai import AzureOpenAI
from django.conf import settings
import paho.mqtt.publish as mqtt_publish

logger = logging.getLogger(__name__)

class ChatInterface:
    def __init__(self):
        self.azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION')
        self.assistant_id = os.getenv('AZURE_OPENAI_ASSISTANT_ID')
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        self.current_thread_id = None
        # System prompt for the model
        self.system_prompt = """You are an AI assistant for a Smart Hotel Management System.
            You must EXTRACT AND USE the EXACT room numbers/IDs mentioned in user messages.

            **ROOM_ID** = Fill this variable with room number which user asked and replace it in the endpoint

            Example conversations:

            1. Room Status Queries:
            User: "What's the status of room 201?"
            Response:
            {
                "action": "api_call",
                "method": "GET",
                "endpoint": "/api/rooms/by-number/201/status/",
                "params": {}
            }

            2. Energy Report Queries:
            User: "Show me energy consumption for room 201"
            Response:
            {
                "action": "api_call",
                "method": "GET",
                "endpoint": "/api/rooms/by-number/201/energy-report/",
                "params": {"days": 1}
            }

            3. AC Control:
            User: "Set temperature to 23 degrees in room 201"
            Response:
            {
                "action": "api_call",
                "method": "POST",
                "endpoint": "/api/rooms/by-number/307/ac/control/",
                "params": {
                    "temperature": 23,
                    "mode": "COOL"
                }
            }

            4. Air Quality Queries:
            User: "Check air quality in room 102"
            Response:
            {
                "action": "api_call",
                "method": "GET",
                "endpoint": "/api/rooms/by-number/102/data/iaq/",
                "params": {}
            }

            5. Presence Detection:
            User: "Is anyone in room 405?"
            Response:
            {
                "action": "api_call",
                "method": "GET",
                "endpoint": "/api/rooms/by-number/405/data/life-being/",
                "params": {}
            }

            6. Lighting Control:
            User: "Turn on the lights in room 506"
            Response:
            {
                "action": "mqtt_publish",
                "topic": "hotel/room/506/lighting",
                "payload": {"status": "ON"}
            }

            CRITICAL RULES:
            1. ALWAYS use the room number from the user's message
            2. NEVER use default room numbers
            3. ALWAYS provide a valid JSON response
            4. NO explanatory text or markdown
            5. ALL room numbers must be extracted from user input
            6. ENSURE all JSON responses are valid and parsable.

            Available API Endpoints:
                - GET /api/rooms/by-number/{room_number}/status/
                - GET /api/rooms/by-number/{room_number}/energy-report/
                - POST /api/rooms/by-number/{room_number}/devices/{device_id}/control/
                - GET /api/rooms/by-number/{room_number}/data/iaq/
                - GET /api/rooms/by-number/{room_number}/data/life-being/
                - GET /api/energy/summary/

            CRITICAL RULES:
                1. ALWAYS use the room number from the user's message in the endpoint
                2. NEVER use room IDs, only use room numbers
                3. Room numbers should be extracted exactly as mentioned by the user
                4. Use the /rooms/by-number/ endpoints for all room-related queries
                5. Always ensure room number is included in the correct part of the URL
                6. For device control, use the device_id parameter as needed (default to 1 for AC)"""

        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

    def process_text(self, message, context=None):
        try:
            if not self.current_thread_id:
                logger.info("Creating new thread")
                thread = self.client.beta.threads.create()
                self.current_thread_id = thread.id
                logger.info(f"Created thread: {self.current_thread_id}")

                # Add the system prompt to the thread
                logger.info("Adding system prompt to thread")
                self.client.beta.threads.messages.create(
                    thread_id=self.current_thread_id,
                    role="assistant",
                    content=self.system_prompt
                )
            else:
                logger.info(f"Using existing thread: {self.current_thread_id}")

            # Add user's message to the thread
            logger.info(f"Adding message to thread: {message}")
            self.client.beta.threads.messages.create(
                thread_id=self.current_thread_id,
                role="user",
                content=message
            )

            # Run the assistant
            logger.info("Starting assistant run")
            run = self.client.beta.threads.runs.create(
                thread_id=self.current_thread_id,
                assistant_id=self.assistant_id
            )
            logger.info(f"Created run: {run.id}")

            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.current_thread_id,
                    run_id=run.id
                )
                logger.info(f"Run status: {run.status}")
                time.sleep(0.5)

            if run.status == "completed":
                # Get the messages
                logger.info("Run completed, retrieving messages")
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.current_thread_id
                )
                
                # Get the latest assistant message
                found_message = False
                for msg in messages.data:
                    if msg.role == "assistant":
                        found_message = True
                        logger.info(f"msg.content type: {type(msg.content)}, value: {msg.content}")
                        
                        if isinstance(msg.content, list):
                            content = ''.join([
                                part.text.value if hasattr(part, 'text') and hasattr(part.text, 'value') else ''
                                for part in msg.content
                            ])
                        else:
                            content = msg.content
                        
                        logger.info(f"Raw assistant response: {content}")
                        
                        # Check if content is None or empty
                        if not content or not content.strip():
                            logger.error("Empty response from assistant")
                            return "Empty response from assistant"

                        # Try to parse as JSON and execute action
                        try:
                            # Clean up content
                            content = content.strip()
                            if content.startswith("```json"):
                                content = content[7:]
                            if content.endswith("```"):
                                content = content[:-3]
                            content = content.strip()
                            
                            logger.info(f"Cleaned content for parsing: {content}")
                            
                            action_data = json.loads(content)
                            logger.info(f"Successfully parsed JSON: {json.dumps(action_data, indent=2)}")
                            
                            # Validate the action data
                            if not isinstance(action_data, dict):
                                logger.error(f"Response is not a dictionary: {type(action_data)}")
                                return "Invalid response format: not a dictionary"

                            if "action" not in action_data:
                                logger.error("Missing 'action' in response")
                                return "Invalid response format: missing action"
                            
                            if action_data["action"] == "api_call":
                                required_fields = ["method", "endpoint"]
                                missing_fields = [field for field in required_fields if field not in action_data]
                                if missing_fields:
                                    logger.error(f"Missing required fields: {missing_fields}")
                                    return f"Invalid API call format: missing {', '.join(missing_fields)}"
                                
                                # Initialize params if not present
                                if "params" not in action_data:
                                    action_data["params"] = {}

                            return action_data
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON Parse Error. Content: '{content}'. Error: {str(e)}")
                            return "Failed to parse assistant's response as valid JSON."

                if not found_message:
                    logger.warning("No assistant message found in response")
                    return "No response from assistant"
            else:
                logger.error(f"Run failed with status: {run.status}")
                return f"Assistant run failed with status: {run.status}"

        except Exception as e:
            logger.error(f"Error in process_text: {str(e)}", exc_info=True)
            return f"Error processing message: {str(e)}"



    def execute_action(self, action_data):
        """Now just validates and returns the action data"""
        action = action_data.get("action")

        if action == "api_call":
            method = action_data.get("method")
            endpoint = action_data.get("endpoint")
            params = action_data.get("params", {})

            if not method or not endpoint:
                return "Invalid API call parameters."

            # Just return the validated action data
            return action_data

        elif action == "mqtt_publish":
            topic = action_data.get("topic")
            payload = action_data.get("payload")

            if not topic or not payload:
                return "Invalid MQTT parameters."

            # Just return the validated action data
            return action_data

        return "Unsupported action type."

    def clear_history(self):
        """Reset conversation history and thread"""
        self.current_thread_id = None
        self.conversation_history = [{"role": "system", "content": self.system_prompt}]
