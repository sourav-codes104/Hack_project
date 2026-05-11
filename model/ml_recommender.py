import spacy
import json
import os
import re

nlp = None


def get_nlp():
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            nlp = None
            print("Warning: Spacy model could not be loaded. ML similarity will be disabled.")
    return nlp

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'destinations.json')

def load_destinations():
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading destinations.json: {e}")
        return []

def get_ml_recommendations(location, interest, budget, duration, place_types="", season="", exclude_places=None):
    """
    ML-based recommendation using Spacy semantic similarity.
    """
    destinations = load_destinations()
    if not destinations:
        return {"destinations": []}

    if exclude_places:
        destinations = [d for d in destinations if d['name'] not in exclude_places]

    # 1. Filter by Budget (Rough estimate)
    try:
        max_budget = float(budget)
        # Assuming budget is for the total duration
        # Filter destinations where estimated cost (daily * duration) is within budget (with 20% buffer)
        destinations = [d for d in destinations if (d['avg_cost_per_day'] * int(duration)) <= (max_budget * 1.2)]
    except:
        pass

    if not destinations:
        # If budget is too tight, reload all but maybe warn? Or just show cheapest.
        destinations = load_destinations()
        destinations.sort(key=lambda x: x['avg_cost_per_day'])
        destinations = destinations[:10]

    # 2. Semantic Similarity
    user_query = f"{interest} {place_types} {season}".strip()
    
    scored_destinations = []
    
    nlp_model = get_nlp()

    if nlp_model and user_query:
        user_doc = nlp_model(user_query.lower())
        for dest in destinations:
            # Create a rich description for matching
            dest_text = f"{dest['name']} {dest['type']} {dest['description']} {dest['tags']}".lower()
            dest_doc = nlp_model(dest_text)
            
            # Calculate similarity
            similarity = user_doc.similarity(dest_doc)
            
            # Boost score if keywords match exactly
            keywords = user_query.lower().split()
            match_count = sum(1 for word in keywords if word in dest_text)
            boost = (match_count / len(keywords)) if keywords else 0
            
            final_score = (similarity * 0.7) + (boost * 0.3)
            scored_destinations.append((dest, final_score))
    else:
        # Fallback to simple keyword matching if Spacy is missing
        for dest in destinations:
            dest_text = f"{dest['name']} {dest['type']} {dest['description']} {dest['tags']}".lower()
            keywords = user_query.lower().split()
            match_count = sum(1 for word in keywords if word in dest_text)
            score = match_count / len(keywords) if keywords else 0
            scored_destinations.append((dest, score))

    # Sort by score
    scored_destinations.sort(key=lambda x: x[1], reverse=True)
    
    # Format the results to match the expected structure
    results = []
    for dest, score in scored_destinations[:5]:
        results.append({
            "name": dest["name"],
            "type": dest["type"],
            "description": dest["description"],
            "estimated_cost": f"₹{dest['avg_cost_per_day'] * int(duration)} for {duration} days",
            "best_season": dest["best_season"],
            "lat": dest["lat"],
            "lng": dest["lng"],
            "highlights": dest["highlights"],
            "distance_from_origin": "Calculated locally"
        })

    return {"destinations": results}

def get_ml_itinerary(destination_name, duration, budget, start_date=""):
    """
    Generate an activity-based itinerary for the selected destination.
    Activities are grouped by category: Sightseeing, Food & Dining,
    Shopping, Activities & Experiences, and Leisure & Relaxation.
    """
    destinations = load_destinations()
    dest = next((d for d in destinations if d['name'] == destination_name), None)
    
    if not dest:
        # Return a generic one if not found in our DB
        return None

    itinerary_data = {}
    try:
        dur = int(duration)
    except:
        dur = 3

    # Activity templates organized by category
    sightseeing_templates = [
        {"place": "{highlight}", "desc": "Explore the iconic {highlight}. A must-visit landmark! 🏛️"},
        {"place": "Heritage Walk in {name}", "desc": "Take a guided heritage walk through the historic streets of {name}. 🚶"},
        {"place": "Panoramic Viewpoint near {name}", "desc": "Enjoy breathtaking views of the {name} landscape from a scenic viewpoint. 🌄"},
    ]
    food_templates = [
        {"place": "Local Street Food Tour", "desc": "Savour the authentic flavours of {name} — from chaat to regional delicacies! 🍲"},
        {"place": "Traditional Restaurant", "desc": "Dine at a highly-rated restaurant serving classic {name} cuisine. 🍽️"},
        {"place": "Café Hopping", "desc": "Relax with local brews and snacks at charming cafés near {name}. ☕"},
    ]
    shopping_templates = [
        {"place": "Local Bazaar", "desc": "Pick up souvenirs, handicrafts and traditional textiles from the vibrant bazaar. 🛍️"},
        {"place": "Artisan Market", "desc": "Discover handmade goods and local art pieces from skilled artisans. 🎨"},
        {"place": "Spice & Tea Market", "desc": "Stock up on aromatic spices and regional teas to take home. 🌿"},
    ]
    activity_templates = [
        {"place": "Adventure Activity near {name}", "desc": "Get your adrenaline pumping with outdoor adventure activities! 🧗"},
        {"place": "Cultural Experience", "desc": "Immerse yourself in local culture — attend a folk show, workshop or ceremony. 🎭"},
        {"place": "Guided Nature Walk", "desc": "Discover the natural beauty and wildlife around {name}. 🌿"},
    ]
    leisure_templates = [
        {"place": "Sunset at {highlight}", "desc": "Wind down with a stunning sunset view at {highlight}. 🌅"},
        {"place": "Spa & Wellness", "desc": "Treat yourself to a relaxing spa session or yoga experience. 🧘"},
        {"place": "Lakeside / Garden Stroll", "desc": "Take a peaceful walk through gardens or by the waterfront. 🌳"},
    ]

    for day in range(1, dur + 1):
        day_key = f"{start_date} (Day {day})" if start_date and day == 1 else f"Day {day}"
        day_plan = []
        
        # Use highlights for activities — cycle through them
        h_idx = (day - 1) % len(dest['highlights'])
        curr_highlight = dest['highlights'][h_idx]
        next_highlight = dest['highlights'][(h_idx + 1) % len(dest['highlights'])]
        
        # Pick templates that vary by day
        sight = sightseeing_templates[(day - 1) % len(sightseeing_templates)]
        food = food_templates[(day - 1) % len(food_templates)]
        shop = shopping_templates[(day - 1) % len(shopping_templates)]
        activity = activity_templates[(day - 1) % len(activity_templates)]
        leisure = leisure_templates[(day - 1) % len(leisure_templates)]

        def _fmt(text):
            return text.replace("{highlight}", curr_highlight).replace("{name}", dest['name'])

        # 🗺️ Sightseeing
        day_plan.append({
            "category": "Sightseeing",
            "icon": "🗺️",
            "time": "8:00 AM – 11:00 AM",
            "place": _fmt(sight["place"]),
            "cost": f"₹{int(dest['avg_cost_per_day'] * 0.25)}",
            "description": _fmt(sight["desc"]),
            "lat": dest['lat'] + (day * 0.002),
            "lng": dest['lng'] + (day * 0.002)
        })
        
        # 🍴 Food & Dining
        day_plan.append({
            "category": "Food & Dining",
            "icon": "🍴",
            "time": "12:00 PM – 1:30 PM",
            "place": _fmt(food["place"]),
            "cost": f"₹{int(dest['avg_cost_per_day'] * 0.25)}",
            "description": _fmt(food["desc"]),
            "lat": dest['lat'] - (day * 0.001),
            "lng": dest['lng'] - (day * 0.001)
        })
        
        # 🛍️ Shopping
        day_plan.append({
            "category": "Shopping",
            "icon": "🛍️",
            "time": "2:00 PM – 4:00 PM",
            "place": _fmt(shop["place"]),
            "cost": f"₹{int(dest['avg_cost_per_day'] * 0.20)}",
            "description": _fmt(shop["desc"]),
            "lat": dest['lat'] + (day * 0.001),
            "lng": dest['lng'] - (day * 0.002)
        })

        # 🎯 Activities & Experiences
        day_plan.append({
            "category": "Activities",
            "icon": "🎯",
            "time": "4:00 PM – 5:30 PM",
            "place": _fmt(activity["place"]),
            "cost": f"₹{int(dest['avg_cost_per_day'] * 0.20)}",
            "description": _fmt(activity["desc"]),
            "lat": dest['lat'] - (day * 0.002),
            "lng": dest['lng'] + (day * 0.001)
        })

        # 🌅 Leisure & Relaxation
        day_plan.append({
            "category": "Leisure",
            "icon": "🌅",
            "time": "5:30 PM – 7:00 PM",
            "place": _fmt(leisure["place"].replace("{highlight}", next_highlight)),
            "cost": f"₹{int(dest['avg_cost_per_day'] * 0.10)}",
            "description": _fmt(leisure["desc"].replace("{highlight}", next_highlight)),
            "lat": dest['lat'],
            "lng": dest['lng']
        })
        
        itinerary_data[day_key] = day_plan

    return {
        "destination": dest["name"],
        "total_estimated_cost": f"₹{dest['avg_cost_per_day'] * dur}",
        "itinerary": itinerary_data,
        "tips": ["Book local transport in advance", "Try the local street food", "Respect local traditions"],
        "packing_list": ["Comfortable walking shoes", "Sunscreen", "Camera", "Local map"]
    }
