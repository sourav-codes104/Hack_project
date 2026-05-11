import joblib
import os
import json
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'travel_model.pkl')
VECTORIZER_PATH = os.path.join(BASE_DIR, 'tfidf_vectorizer.pkl')
DESTINATIONS_PATH = os.path.join(BASE_DIR, '..', 'data', 'destinations.json')

def predict_category(query):
    """
    Predict the travel category from user query using the trained ML model.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        print("⚠️ Model not trained. Run train_model.py first.")
        return None

    try:
        model = joblib.load(MODEL_PATH)
        tfidf = joblib.load(VECTORIZER_PATH)
        
        X = tfidf.transform([query.lower()])
        prediction = model.predict(X)[0]
        
        # Get probability to ensure confidence
        probs = model.predict_proba(X)
        max_prob = max(probs[0])
        
        print(f"🔮 ML Prediction: {prediction} (Confidence: {max_prob:.2f})")
        
        if max_prob < 0.2: # Low confidence fallback
            return None
            
        return prediction
    except Exception as e:
        print(f"❌ Prediction Error: {e}")
        return None

def get_trained_recommendations(query, budget, duration, exclude_places=None):
    """
    Get recommendations instantly using the trained ML model.
    """
    category = predict_category(query)
    
    try:
        with open(DESTINATIONS_PATH, 'r', encoding='utf-8') as f:
            all_destinations = json.load(f)
    except:
        return []

    # 1. Filter out already excluded places
    if exclude_places:
        all_destinations = [d for d in all_destinations if d['name'] not in exclude_places]

    # 2. Filter by predicted category
    if category:
        # Match by type (substring) or tags
        matches = [d for d in all_destinations if category.lower() in d['type'].lower() or category.lower() in d['tags'].lower()]
    else:
        matches = all_destinations

    # 3. Filter by budget (with a generous 50% buffer to avoid empty results)
    try:
        max_budget = float(budget)
        budget_matches = [d for d in matches if (d['avg_cost_per_day'] * int(duration)) <= (max_budget * 1.5)]
        if len(budget_matches) >= 3:
            matches = budget_matches
        # else: stick with 'matches' to keep variety
    except:
        pass

    # 4. Return exactly 5 if possible, or all if less
    if len(matches) > 5:
        matches = random.sample(matches, 5)
    elif not matches and all_destinations:
        # Emergency fallback to any available destinations
        matches = random.sample(all_destinations, min(5, len(all_destinations)))

    # 5. Format for UI
    results = []
    for d in matches:
        results.append({
            "name": d["name"],
            "type": d["type"],
            "description": f"✨ Recommended via Local ML: {d['description']}",
            "estimated_cost": f"₹{d['avg_cost_per_day'] * int(duration)} for {duration} days",
            "best_season": d["best_season"],
            "lat": d["lat"],
            "lng": d["lng"],
            "highlights": d["highlights"],
            "distance_from_origin": "Local Prediction"
        })
        
    return {"destinations": results}
