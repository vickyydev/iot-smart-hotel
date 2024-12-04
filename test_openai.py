# test_openai.py

from openai import AzureOpenAI
import os

# Set up Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
)

deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

# Create a chat completion
response = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ],
)

# Print the assistant's reply
print(response.choices[0].message.content.strip())
