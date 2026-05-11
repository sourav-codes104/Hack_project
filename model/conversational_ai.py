import os
import google.generativeai as genai
from dotenv import load_dotenv

# -----------------------------------------------------
# 🔹 Load API Key and Configure Gemini
# -----------------------------------------------------
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# ✅ Updated Gemini Model (Stable)
model = genai.GenerativeModel(
    "gemini-2.0-flash",
    system_instruction="""You are TravelMate AI — a smart, friendly, and knowledgeable travel assistant specializing in Indian tourism.

Your rules:
1. Always answer the user's ACTUAL question directly and specifically.
2. If the user asks about a specific place (e.g., "Tell me about Jaipur"), give detailed info about THAT place.
3. If the user asks a general question (e.g., "Hi", "How are you?"), respond naturally and conversationally.
4. If the user asks for recommendations, suggest real places with practical details.
5. Use Markdown formatting: headers (##), bullet points, bold text, and emojis.
6. Keep responses concise (3-6 short paragraphs max) unless the user asks for detailed info.
7. Never say "as an AI model" or "I don't have personal experiences".
8. Always be enthusiastic about travel!

Response format for travel queries:
## 🏖 [Topic/Place Name]
Brief engaging intro.

## 📍 Key Highlights
- Bullet points with useful info
- Include emojis for categories

## 💡 Pro Tips
1-2 practical tips.
"""
)

# ✅ Use Gemini's built-in chat session for proper conversation memory
chat_session = model.start_chat(history=[]) if api_key else None


# -----------------------------------------------------
# 🔹 Main Chat Function
# -----------------------------------------------------
def chat_with_gemini(user_input):
    """
    Handles conversation with Gemini AI using proper chat session.
    Maintains real conversation context automatically.
    """
    global chat_session

    if not api_key:
        return "Gemini AI is not configured yet. Please set GEMINI_API_KEY in the deployment environment."

    try:
        if chat_session is None:
            chat_session = model.start_chat(history=[])

        # 💬 Send message using chat session (maintains context automatically)
        response = chat_session.send_message(user_input)

        # 🧩 Extract the text safely
        if hasattr(response, "text"):
            ai_reply = response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            ai_reply = response.candidates[0].content.parts[0].text.strip()
        else:
            ai_reply = "⚠️ No response received. Please try again."

        # 🔄 Reset chat if history gets too long (prevent token overflow)
        if len(chat_session.history) > 20:
            chat_session = model.start_chat(history=chat_session.history[-10:])

        return ai_reply

    except Exception as e:
        print(f"❌ Chat Error: {e}")
        # Reset session on error to prevent stuck state
        chat_session = model.start_chat(history=[])
        return "Sorry, I ran into a temporary issue. Please try again! 🔄"


# -----------------------------------------------------
# ✅ Optional Debugging (Run directly)
# -----------------------------------------------------
if __name__ == "__main__":
    print(chat_with_gemini("Tell me about ancient temples near Mathura"))
