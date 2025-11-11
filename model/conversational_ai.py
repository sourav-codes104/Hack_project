import os
import google.generativeai as genai
from dotenv import load_dotenv
from model.ner_utils import extract_places

# -----------------------------------------------------
# 🔹 Load API Key and Configure Gemini
# -----------------------------------------------------
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file!")

genai.configure(api_key=api_key)

# ✅ Updated Gemini Model (Stable as of Nov 2025)
model = genai.GenerativeModel("gemini-2.5-flash")

# ✅ Store short-term conversation memory
conversation_history = []


# -----------------------------------------------------
# 🔹 Location Detection (NER)
# -----------------------------------------------------
def detect_location_from_text(user_input):
    """Extract location names using spaCy (from ner_utils)."""
    places = extract_places(user_input)
    return places[0] if places else None


# -----------------------------------------------------
# 🔹 Main Chat Function (With Markdown Output)
# -----------------------------------------------------
def chat_with_gemini(user_input):
    """
    Handles conversation with Gemini AI.
    Includes memory, location detection, and Markdown-optimized responses.
    """
    global conversation_history

    try:
        # 🧭 Try to auto-detect any location name in the user query
        detected_place = detect_location_from_text(user_input)
        if detected_place:
            conversation_history.append({
                "role": "system",
                "content": f"Detected location: {detected_place}"
            })

        # 🧠 Add user message
        conversation_history.append({"role": "user", "content": user_input})

        # ✨ System prompt for AI formatting and tone
        system_prompt = """
        You are an intelligent, friendly travel assistant AI.
        Always reply in **Markdown** format using the following structure:
        ---
        ## 🏖 Overview
        Short, engaging introduction.

        ## 📍 Key Places / Insights
        - Bullet points or short numbered list.
        - Include emojis for categories (⛩️, 🌆, 🏞️, 🍴, ✈️).

        ## 💡 Tips or Summary
        1-2 practical travel tips, safety notes, or local highlights.

        ✅ Keep tone natural and professional.
        ✅ Avoid long blocks of text — use spacing & lists.
        ✅ Never say “as an AI model”.
        ---
        """

        # 🧾 Combine context messages
        messages = [system_prompt] + [msg["content"] for msg in conversation_history]

        # 💬 Generate response using Gemini
        response = model.generate_content(contents=messages)

        # 🧩 Extract the text safely
        if hasattr(response, "text"):
            ai_reply = response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            ai_reply = response.candidates[0].content.parts[0].text.strip()
        else:
            ai_reply = "⚠️ No AI response received."

        # 🧠 Save AI reply into history
        conversation_history.append({"role": "assistant", "content": ai_reply})

        # 🔄 Keep memory short (avoid overload)
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]

        return ai_reply

    except Exception as e:
        print("❌ Chat Error:", e)
        return "Sorry, I ran into an issue while connecting to Gemini AI."


# -----------------------------------------------------
# ✅ Optional Debugging (Run directly)
# -----------------------------------------------------
if __name__ == "__main__":
    print(chat_with_gemini("Tell me about ancient temples near Mathura"))