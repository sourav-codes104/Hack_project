from model.ml_recommender import get_ml_recommendations

def test_ml():
    print("Testing ML Recommender...")
    
    # Test case 1: Mountains and Adventure
    print("\n--- Test 1: Mountains & Adventure ---")
    results = get_ml_recommendations("Delhi", "mountains and adventure", "20000", "5", "Hill Station", "Summer")
    for d in results.get('destinations', []):
        print(f"- {d['name']} ({d['type']}): {d['description'][:60]}...")

    # Test case 2: Spiritual and Peaceful
    print("\n--- Test 2: Spiritual & Peaceful ---")
    results = get_ml_recommendations("Mumbai", "spiritual and peaceful temple", "10000", "3", "Spiritual", "Winter")
    for d in results.get('destinations', []):
        print(f"- {d['name']} ({d['type']}): {d['description'][:60]}...")

    # Test case 3: Beach and Party
    print("\n--- Test 3: Beach & Party ---")
    results = get_ml_recommendations("Bangalore", "beach party nightlife", "30000", "4", "Beach", "Winter")
    for d in results.get('destinations', []):
        print(f"- {d['name']} ({d['type']}): {d['description'][:60]}...")

if __name__ == "__main__":
    test_ml()
