def get_recommendations(location, interest, budget):
    data = [
        {"place": "Rajwada Palace", "desc": "Historic royal palace", "budget": "medium"},
        {"place": "Lal Bagh Palace", "desc": "Beautiful architecture and history", "budget": "high"},
        {"place": "Choral Dam", "desc": "Peaceful natural retreat", "budget": "low"}
    ]
    results = [d for d in data if interest.lower() in d["desc"].lower() or budget.lower() in d["budget"].lower()]
    return results if results else data
