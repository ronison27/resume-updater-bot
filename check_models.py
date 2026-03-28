from google import genai
from google.genai import types

client = genai.Client(api_key="your_key")

# Multi-turn chat
chat = client.chats.create(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a resume expert.",
        temperature=0.7
    )
)

# First message
response1 = chat.send_message("Analyze this resume...")
print(response1.text)

# Follow up
response2 = chat.send_message("Now rewrite the summary section")
print(response2.text)