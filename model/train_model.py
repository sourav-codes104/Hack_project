import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'training_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'travel_model.pkl')
VECTORIZER_PATH = os.path.join(BASE_DIR, 'tfidf_vectorizer.pkl')

def train_model():
    print("🚀 Starting ML Model Training...")
    
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: Training data not found at {DATA_PATH}")
        return

    # 1. Load Data
    try:
        df = pd.read_csv(DATA_PATH)
        print(f"📊 Loaded {len(df)} training examples.")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return

    # 2. Vectorization (Convert text to numbers)
    print("🔡 Vectorizing text data...")
    tfidf = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    X = tfidf.fit_transform(df['query'])
    y = df['category']

    # 3. Train Classifier
    print("🧠 Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # 4. Save Model and Vectorizer
    print("💾 Saving model and vectorizer...")
    joblib.dump(model, MODEL_PATH)
    joblib.dump(tfidf, VECTORIZER_PATH)
    
    print("✅ Training Complete! Model saved as 'travel_model.pkl'")

if __name__ == "__main__":
    train_model()
