import os
import google.generativeai as genai
from dotenv import load_dotenv

# ✅ Load your Gemini API key from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Initialize Gemini model (latest stable)
model = genai.GenerativeModel("gemini-flash-latest")

def get_chat_response(user_msg):
    try:
        # 🧠 Read the context file
        with open("data/travel_context.txt", "r", encoding="utf-8") as f:
            context = f.read()

        # Combine user input + your dataset
        prompt = f"""
        You are an AI Travel Assistant.
        Use the context data below to answer questions accurately and naturally.

        Context:
        {context}

        User: {user_msg}
        """

        # Send to Gemini AI
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"⚠️ Error: {str(e)}"
