import os
import google.generativeai as genai
from dotenv import load_dotenv

# ✅ Load .env from root directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def get_recommendations(location, interest, budget, travel_mode="car"):
    try:
        print("----------------------------------------------------")
        print("📍 Location:", location)
        print("🎯 Interest:", interest)
        print("💰 Budget:", budget)
        print("🚗 Mode:", travel_mode)
        print("----------------------------------------------------")

        # ✅ Updated & Supported Model (as of Nov 2025)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # ✅ AI prompt
        prompt = (
            f"You are an AI travel assistant. Suggest 3 amazing travel destinations "
            f"in or near {location} for someone who loves {interest}, has a {budget} budget, "
            f"and will travel by {travel_mode}. Keep it short, creative, and include emojis."
        )

        print("🧠 Sending prompt to Gemini 2.5...\n", prompt)
        print("----------------------------------------------------")

        # ✅ Generate AI response
        response = model.generate_content(prompt)
        ai_reply = getattr(response, "text", "No AI response received").strip()

        print("✅ Gemini 2.5 Response Received ✅")
        print(ai_reply)
        print("----------------------------------------------------")

        return ai_reply

    except Exception as e:
        print("❌ ERROR OCCURRED:")
        print(str(e))
        print("----------------------------------------------------")
        return "Sorry, I couldn't fetch AI recommendations right now."
