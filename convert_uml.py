import base64
import requests
import img2pdf
import os

diagrams = {
    "class_diagram": """classDiagram
    class User {
        +int userid
        +string name
        +string email
        +float budget
        +int travel_days
        +string password
        +login(username, password)
        +create(username, password, email)
        +enterPreferences(budget, travel_days, place_types, season)
        +viewRecommendations()
    }

    class Destination {
        +string name
        +string category
        +float cost_exp
        +string details
        +get_by_name(name)
    }

    class Accommodation {
        +int acc_id
        +string name
        +float price
        +string location
        +get_by_location(location)
    }

    class TravelPlan {
        +int planid
        +string destination_name
        +float total_cost
        +int duration
        +string itinerary_json
        +createPlan(user_id, destination_name, duration, total_cost, ...)
        +getUserHistory(user_id)
        +deletePlan(plan_id, user_id)
    }

    class RecommendationEngine {
        +analyzePreferences(budget, travel_days, interest, ...)
        +matchDestinationData(location, constraints)
        +suggestDestinations(location, interest, budget, travel_mode, ...)
    }

    class RecommenderModule {
        +get_recommendations(location, interest, budget, ...)
        +get_more_recommendations(location, interest, budget, ...)
        +get_detailed_itinerary(location, destination, ...)
    }

    class GeminiAPI {
        <<Service>>
        +generate_content(prompt)
    }

    User "1" --> "*" TravelPlan : creates
    TravelPlan --> Destination : targets
    RecommendationEngine ..> RecommenderModule : uses
    RecommenderModule ..> GeminiAPI : calls
    TravelPlan ..> Accommodation : books""",
    "recommendation_flow": """sequenceDiagram
    actor User
    participant FlaskApp as app.py
    participant Engine as RecommendationEngine
    participant Recommender as recommender.py
    participant Gemini as Gemini AI API
    participant DB as SQLite Database

    User->>FlaskApp: POST /recommend (location, interest, budget)
    FlaskApp->>DB: Update User Preferences
    FlaskApp->>Engine: suggestDestinations(...)
    Engine->>Recommender: get_recommendations(...)
    Recommender->>Gemini: generate_content(prompt)
    Gemini-->>Recommender: JSON Response (5 Destinations)
    Recommender-->>Engine: Structured Data
    Engine-->>FlaskApp: Results List
    FlaskApp->>User: Render result.html""",
    "chatbot_interaction": """sequenceDiagram
    actor User
    participant FlaskApp as app.py
    participant ChatAI as conversational_ai.py
    participant NER as ner_utils.py
    participant Gemini as Gemini AI API

    User->>FlaskApp: POST /ai_chat (message)
    FlaskApp->>ChatAI: chat_with_gemini(message)
    ChatAI->>NER: extract_places(message)
    NER-->>ChatAI: Detected Locations
    ChatAI->>Gemini: generate_content(context + message)
    Gemini-->>ChatAI: Markdown Reply
    ChatAI-->>FlaskApp: reply
    FlaskApp-->>User: JSON {reply: ...}""",
    "database_schema": """erDiagram
    USER ||--o{ TRAVEL_PLAN : has
    USER ||--o{ FEEDBACK : gives
    TRAVEL_PLAN ||--|| DESTINATION : visits
    TRAVEL_PLAN ||--o{ BOOKING : includes
    ACCOMMODATION ||--o{ BOOKING : reserved_in

    USER {
        int user_id PK
        string name
        string email
        string password
        float budget
        int travel_days
    }

    TRAVEL_PLAN {
        int plan_id PK
        int user_id FK
        string destination_name
        float total_cost
        int duration
        string itinerary_json
        datetime created_at
    }

    DESTINATION {
        int destination_id PK
        string name
        string type
        float average_cost
    }

    ACCOMMODATION {
        int accommodation_id PK
        string name
        float price
        string location
    }

    FEEDBACK {
        int id PK
        string name
        string email
        string message
    }"""
}

def generate_pdf(name, code):
    # Encode code to base64
    sample_string_bytes = code.encode("ascii")
    base64_bytes = base64.b64encode(sample_string_bytes)
    base64_string = base64_bytes.decode("ascii")
    
    url = f"https://mermaid.ink/img/{base64_string}"
    print(f"Fetching {name} from {url}...")
    
    response = requests.get(url)
    if response.status_code == 200:
        img_path = f"{name}.png"
        pdf_path = f"{name}.pdf"
        
        with open(img_path, "wb") as f:
            f.write(response.content)
            
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(img_path))
            
        os.remove(img_path)
        print(f"✅ Created {pdf_path}")
    else:
        print(f"❌ Failed to fetch {name}")

for name, code in diagrams.items():
    generate_pdf(name, code)
