import os
import google.generativeai as genai

API_KEY = "AIzaSyCF7WqhgxNed-0uaMd4yWZRUurG56DEd4M"  # The latest key provided
print(f"Testing API Key: {API_KEY[:5]}...")

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3-pro-preview')
    response = model.generate_content("Hello, are you working?")
    print("SUCCESS! API Response:")
    print(response.text)
except Exception as e:
    print("FAILURE! Error details:")
    print(e)
