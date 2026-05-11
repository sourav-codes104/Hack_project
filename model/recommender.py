import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

def detect_location_from_text(user_input):
    from model.ner_utils import extract_places

    places = extract_places(user_input)
    if places:
        return places[0]  # just take first one
    return None

# ✅ Load .env from root directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)


def get_recommendations(location, interest, budget, travel_mode="car", duration=3, place_types="", season="", start_date="", end_date=""):
    """
    Generate 5 destination suggestions based on user preferences.
    Hierarchy: 1. Trained ML Model -> 2. Spacy Semantic -> 3. Gemini AI
    """
    try:
        from model.ml_recommender import get_ml_recommendations
        from model.trained_recommender import get_trained_recommendations

        # --- 🚀 LEVEL 1: TRAINED ML MODEL (Instant) ---
        print("--- 🔮 Attempting Trained ML Model ---")
        trained_results = get_trained_recommendations(f"{interest} {place_types}", budget, duration)
        
        if trained_results and trained_results.get("destinations"):
            print("✅ Trained ML Model Successful!")
            return trained_results

        # --- 🤖 LEVEL 2: SPACY SEMANTIC (Fallback 1) ---
        print("--- 🤖 Attempting Semantic Similarity ---")
        ml_results = get_ml_recommendations(location, interest, budget, duration, place_types, season)
        
        if ml_results and ml_results.get("destinations"):
            print("✅ ML Recommendation Successful!")
            return ml_results
            
        print("⚠️ ML returned no results. Falling back to Gemini...")
        
        print("----------------------------------------------------")
        print("📍 Location:", location)
        print("🎯 Interest:", interest)
        print("💰 Budget: ₹", budget)
        print("🚗 Mode:", travel_mode)
        print("⏱️ Duration:", duration, "days")
        print("🏖️ Place Types:", place_types)
        print("🌤️ Season:", season)
        print("----------------------------------------------------")

        model = genai.GenerativeModel("gemini-flash-latest")

        place_types_str = place_types if place_types else "any type"
        season_str = season if season else "any season"

        prompt = (
            f"You are an expert AI travel planner. A user from {location} wants to travel.\n"
            f"Their preferences:\n"
            f"- Budget: ₹{budget} (Indian Rupees)\n"
            f"- Duration: {duration} days\n"
            f"- Interests: {interest}\n"
            f"- Preferred place types: {place_types_str}\n"
            f"- Preferred season: {season_str}\n"
            f"- Travel Dates: {start_date} to {end_date}\n"
            f"- Travel mode: {travel_mode}\n\n"
            f"Suggest exactly 5 travel destinations that match these preferences.\n"
            f"For each destination, include approximate latitude and longitude coordinates.\n\n"
            f"IMPORTANT: Return ONLY a valid JSON object with no markdown formatting (no ```json).\n"
            f"Use this exact structure:\n"
            f'{{\n'
            f'  "destinations": [\n'
            f'    {{\n'
            f'      "name": "Destination Name",\n'
            f'      "type": "Beach/Hill/Mountain/etc",\n'
            f'      "description": "2-3 sentence engaging description with emojis",\n'
            f'      "estimated_cost": "₹XXXX for {duration} days",\n'
            f'      "best_season": "Best time to visit",\n'
            f'      "lat": 12.3456,\n'
            f'      "lng": 78.9012,\n'
            f'      "highlights": ["highlight 1", "highlight 2", "highlight 3"],\n'
            f'      "distance_from_origin": "approx distance from {location}"\n'
            f'    }}\n'
            f'  ]\n'
            f'}}\n'
            f"Make sure all 5 places are realistic, within the budget, and accessible by {travel_mode}."
        )

        print("🧠 Sending prompt to Gemini...\n")

        response = model.generate_content(prompt)
        ai_reply = getattr(response, "text", "{}").strip()

        # Robust JSON extraction using regex
        json_match = re.search(r'\{.*\}', ai_reply, re.DOTALL)
        if json_match:
            ai_reply = json_match.group(0)
        else:
            ai_reply = ai_reply.strip()

        print("✅ Gemini Response Received ✅")
        print(ai_reply[:500])
        print("----------------------------------------------------")

        try:
            structured_data = json.loads(ai_reply)
            if "destinations" not in structured_data or not structured_data["destinations"]:
                 raise ValueError("Missing destinations key")
            return structured_data
        except (json.JSONDecodeError, ValueError):
            print("⚠️ AI parsing failed. Using fallback.")
            return self_get_fallback_recommendations(location, duration, budget)

    except Exception as e:
        print("❌ AI Error:", str(e))
        return self_get_fallback_recommendations(location, duration, budget)

def self_get_fallback_recommendations(location, duration, budget):
    """Safety fallback to ensure the UI never breaks."""
    return {
        "destinations": [
            {
                "name": "Jaipur", "type": "Heritage", "lat": 26.9124, "lng": 75.7873,
                "description": "The Pink City awaits with its royal palaces and vibrant markets! 🏰",
                "estimated_cost": f"₹{int(float(budget)*0.6)} for {duration} days",
                "best_season": "October to March",
                "highlights": ["Amer Fort", "Hawa Mahal", "City Palace"],
                "distance_from_origin": "Varies"
            },
            {
                "name": "Goa", "type": "Beach", "lat": 15.2993, "lng": 74.1240,
                "description": "Sun, sand, and serenity! Explore the best beaches of India. 🏖️",
                "estimated_cost": f"₹{int(float(budget)*0.8)} for {duration} days",
                "best_season": "November to February",
                "highlights": ["Calangute Beach", "Fort Aguada", "Old Goa"],
                "distance_from_origin": "Varies"
            },
            {
                "name": "Manali", "type": "Hill Station", "lat": 32.2432, "lng": 77.1892,
                "description": "Snow-capped peaks and adventurous trails in the heart of Himalayas. 🏔️",
                "estimated_cost": f"₹{int(float(budget)*0.7)} for {duration} days",
                "best_season": "March to June",
                "highlights": ["Rohtang Pass", "Solang Valley", "Hadimba Temple"],
                "distance_from_origin": "Varies"
            },
            {
                "name": "Varanasi", "type": "Spiritual", "lat": 25.3176, "lng": 82.9739,
                "description": "Experience the spiritual heart of India on the banks of Ganga. 🪔",
                "estimated_cost": f"₹{int(float(budget)*0.4)} for {duration} days",
                "best_season": "October to March",
                "highlights": ["Kashi Vishwanath", "Ganga Aarti", "Sarnath"],
                "distance_from_origin": "Varies"
            },
            {
                "name": "Munnar", "type": "Nature", "lat": 10.0889, "lng": 77.0595,
                "description": "Lush tea gardens and misty hills in God's Own Country. 🍵",
                "estimated_cost": f"₹{int(float(budget)*0.5)} for {duration} days",
                "best_season": "September to March",
                "highlights": ["Tea Museum", "Eravikulam National Park", "Mattupetty Dam"],
                "distance_from_origin": "Varies"
            }
        ]
    }


def get_more_recommendations(location, interest, budget, travel_mode, duration, place_types, season, exclude_places, start_date="", end_date=""):
    """
    Get 5 more suggestions, excluding already-shown places.
    Uses Local ML first, then falls back to Gemini.
    """
    try:
        from model.trained_recommender import get_trained_recommendations

        # --- 🚀 LEVEL 1: TRAINED ML MODEL (Instant) ---
        print("--- 🔮 Attempting Trained ML Model (More) ---")
        trained_results = get_trained_recommendations(f"{interest} {place_types}", budget, duration, exclude_places=exclude_places)
        
        if trained_results and trained_results.get("destinations"):
            print("✅ Trained ML Model Successful!")
            return trained_results

        print("⚠️ ML failed for more. Falling back to Gemini...")
        model = genai.GenerativeModel("gemini-flash-latest")

        place_types_str = place_types if place_types else "any type"
        season_str = season if season else "any season"
        exclude_str = ", ".join(exclude_places) if exclude_places else "none"

        prompt = (
            f"You are an expert AI travel planner. A user from {location} wants more travel suggestions.\n"
            f"Their preferences:\n"
            f"- Budget: ₹{budget} (Indian Rupees)\n"
            f"- Duration: {duration} days\n"
            f"- Interests: {interest}\n"
            f"- Preferred place types: {place_types_str}\n"
            f"- Preferred season: {season_str}\n"
            f"- Travel Dates: {start_date} to {end_date}\n"
            f"- Travel mode: {travel_mode}\n\n"
            f"ALREADY SUGGESTED (do NOT repeat these): {exclude_str}\n\n"
            f"Suggest exactly 5 NEW and DIFFERENT travel destinations.\n"
            f"For each destination, include approximate latitude and longitude coordinates.\n\n"
            f"IMPORTANT: Return ONLY a valid JSON object with no markdown formatting (no ```json).\n"
            f"Use this exact structure:\n"
            f'{{\n'
            f'  "destinations": [\n'
            f'    {{\n'
            f'      "name": "Destination Name",\n'
            f'      "type": "Beach/Hill/Mountain/etc",\n'
            f'      "description": "2-3 sentence engaging description with emojis",\n'
            f'      "estimated_cost": "₹XXXX for {duration} days",\n'
            f'      "best_season": "Best time to visit",\n'
            f'      "lat": 12.3456,\n'
            f'      "lng": 78.9012,\n'
            f'      "highlights": ["highlight 1", "highlight 2", "highlight 3"],\n'
            f'      "distance_from_origin": "approx distance from {location}"\n'
            f'    }}\n'
            f'  ]\n'
            f'}}'
        )

        response = model.generate_content(prompt)
        ai_reply = getattr(response, "text", "{}").strip()

        json_match = re.search(r'\{.*\}', ai_reply, re.DOTALL)
        if json_match:
            ai_reply = json_match.group(0)
        else:
            ai_reply = ai_reply.strip()

        try:
            return json.loads(ai_reply)
        except json.JSONDecodeError:
            return {"error": "AI response was not valid JSON."}

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {"error": "Could not fetch more recommendations."}


def get_detailed_itinerary(location, destination, interest, budget, travel_mode, duration, season="", start_date="", end_date=""):
    """
    Generate a detailed day-wise itinerary for a selected destination.
    Uses Local ML/Templates first, then falls back to Gemini AI.
    """
    try:
        from model.ml_recommender import get_ml_itinerary

        print(f"--- 🤖 Attempting ML Itinerary for {destination} ---")
        ml_itinerary = get_ml_itinerary(destination, duration, budget, start_date)
        
        if ml_itinerary:
            print("✅ ML Itinerary Successful!")
            return ml_itinerary
            
        print("⚠️ ML Itinerary failed. Falling back to Gemini...")

        model = genai.GenerativeModel("gemini-flash-latest")
        season_str = season if season else "any season"

        prompt = (
            f"You are an expert AI travel planner. Create a detailed {duration}-day travel itinerary\n"
            f"for visiting {destination} (traveling from {location}).\n"
            f"User preferences:\n"
            f"- Budget: ₹{budget} (Indian Rupees)\n"
            f"- Travel mode: {travel_mode}\n"
            f"- Interests: {interest}\n"
            f"- Travel Dates: {start_date} to {end_date}\n"
            f"- Season: {season_str}\n\n"
            f"IMPORTANT: Organize activities by CATEGORY and include a suggested TIME for each.\n"
            f"Categories: Sightseeing, Food & Dining, Shopping, Activities, Leisure.\n"
            f"Each activity must have 'category', 'icon', and 'time' fields.\n\n"
            f"IMPORTANT: Return ONLY a valid JSON object with no markdown formatting (no ```json).\n"
            f"Use this exact structure:\n"
            f'{{\n'
            f'  "destination": "{destination}",\n'
            f'  "total_estimated_cost": "₹XXXX",\n'
            f'  "itinerary": {{\n'
            f'    "{start_date} (Day 1)": [\n'
            f'      {{"category": "Sightseeing", "icon": "🗺️", "time": "8:00 AM \u2013 11:00 AM", "place": "Place Name", "cost": "₹XXX", "description": "Engaging description with emojis", "lat": 12.34, "lng": 78.90}},\n'
            f'      {{"category": "Food & Dining", "icon": "🍴", "time": "12:00 PM \u2013 1:30 PM", "place": "...", "cost": "...", "description": "...", "lat": 0, "lng": 0}},\n'
            f'      {{"category": "Shopping", "icon": "🛍️", "time": "2:00 PM \u2013 4:00 PM", "place": "...", "cost": "...", "description": "...", "lat": 0, "lng": 0}},\n'
            f'      {{"category": "Activities", "icon": "🎯", "time": "4:00 PM \u2013 5:30 PM", "place": "...", "cost": "...", "description": "...", "lat": 0, "lng": 0}},\n'
            f'      {{"category": "Leisure", "icon": "🌅", "time": "5:30 PM \u2013 7:00 PM", "place": "...", "cost": "...", "description": "...", "lat": 0, "lng": 0}}\n'
            f'    ],\n'
            f'    "Day 2": [...]\n'
            f'  }},\n'
            f'  "tips": ["tip1", "tip2", "tip3"],\n'
            f'  "packing_list": ["item1", "item2"]\n'
            f'}}\n'
            f"Include realistic places in and around {destination}. Ensure total cost fits ₹{budget}."
        )

        response = model.generate_content(prompt)
        ai_reply = getattr(response, "text", "{}").strip()

        json_match = re.search(r'\{.*\}', ai_reply, re.DOTALL)
        if json_match:
            ai_reply = json_match.group(0)
        else:
            ai_reply = ai_reply.strip()

        print("✅ Detailed itinerary received for", destination)

        try:
            return json.loads(ai_reply)
        except json.JSONDecodeError:
            print("⚠️ AI parsing failed for itinerary. Using fallback.")
            return self_get_fallback_itinerary(destination, duration, budget, start_date)

    except Exception as e:
        print("❌ Itinerary ERROR:", str(e))
        return self_get_fallback_itinerary(destination, duration, budget, start_date)

def self_get_fallback_itinerary(destination, duration, budget, start_date):
    """Safety fallback to ensure the itinerary UI never breaks."""
    itinerary_data = {}
    
    try:
        duration = max(1, int(duration))
    except (ValueError, TypeError):
        duration = 3
        
    try:
        budget_val = float(budget)
    except (ValueError, TypeError):
        budget_val = 5000.0

    for day in range(1, duration + 1):
        day_key = f"{start_date} (Day {day})" if start_date and day == 1 else f"Day {day}"
        itinerary_data[day_key] = [
            {
                "category": "Sightseeing",
                "icon": "🗺️",
                "time": "8:00 AM – 11:00 AM",
                "place": f"Explore {destination}",
                "cost": f"₹{int(budget_val * 0.1 / duration)}",
                "description": f"Start your day exploring the heart of {destination} and its popular landmarks. 🏙️",
                "lat": 0,
                "lng": 0
            },
            {
                "category": "Food & Dining",
                "icon": "🍴",
                "time": "12:00 PM – 1:30 PM",
                "place": "Local Cuisine Experience",
                "cost": f"₹{int(budget_val * 0.1 / duration)}",
                "description": f"Enjoy authentic local cuisine and regional specialties of {destination}. 🍛",
                "lat": 0,
                "lng": 0
            },
            {
                "category": "Shopping",
                "icon": "🛍️",
                "time": "2:00 PM – 4:00 PM",
                "place": "Local Market & Souvenirs",
                "cost": f"₹{int(budget_val * 0.1 / duration)}",
                "description": "Browse local markets for souvenirs, handicrafts and traditional items. 🛒",
                "lat": 0,
                "lng": 0
            },
            {
                "category": "Activities",
                "icon": "🎯",
                "time": "4:00 PM – 5:30 PM",
                "place": f"Cultural Experience in {destination}",
                "cost": f"₹{int(budget_val * 0.05 / duration)}",
                "description": "Immerse yourself in local culture and traditions. 🎭",
                "lat": 0,
                "lng": 0
            },
            {
                "category": "Leisure",
                "icon": "🌅",
                "time": "5:30 PM – 7:00 PM",
                "place": "Sunset Viewpoint / Leisure",
                "cost": f"₹{int(budget_val * 0.05 / duration)}",
                "description": "Catch a beautiful sunset or enjoy a relaxing walk to end the day. 🌇",
                "lat": 0,
                "lng": 0
            }
        ]

    return {
        "destination": destination,
        "total_estimated_cost": f"₹{budget}",
        "itinerary": itinerary_data,
        "tips": ["Carry local currency", "Stay hydrated", "Respect local customs"],
        "packing_list": ["Comfortable shoes", "Camera", "Power bank", "Weather-appropriate clothing"]
    }
