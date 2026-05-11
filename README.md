# 🌍 AI TravelMate

An AI-powered travel assistant that helps users discover destinations, plan trips, and interact naturally through conversational AI.

---

## 🚀 Features
- 🧠 AI chatbot for travel planning and conversation
- 🗺️ Destination recommendations based on user preferences
- ☁️ Weather-aware trip suggestions using OpenWeatherMap
- 💬 Multi-modal chat support with voice/text input
- 🧾 Session history and itinerary preview

---

## 🧩 Tech Stack
- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, Flask
- **AI Modules:** NLP, NER, recommender system
- **APIs:** OpenWeatherMap, Google Maps

---

## ⚙️ Setup Instructions
```bash
git clone https://github.com/sourav-codes104/Hack_project.git
cd Hack_project
python -m venv myenv
myenv\Scripts\activate      # Windows PowerShell: .\myenv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

---

## ▶️ Usage
1. Start the app with `python app.py`
2. Open `http://127.0.0.1:5000` in your browser
3. Use the chat interface to ask for travel recommendations, weather updates, or itinerary ideas

---

## ☁️ Deploy to Render
- Ensure the project is pushed to a Git repository connected to Render
- Add the following environment variables in Render:
  - `GEMINI_API_KEY`
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
- Render will install dependencies from `requirements.txt` and run the app with Gunicorn

---

## 📁 Project structure
- `app.py` — Flask application entry point
- `model/` — NLP, recommender, and chatbot logic
- `static/` — CSS, JavaScript, and frontend assets
- `templates/` — HTML views for the app
- `utils/` — helper modules for maps, weather, and database setup
- `database/` — exported user and feedback data
- `data/` — training data and travel destination metadata

---

## 💡 Notes
- Ensure the Python environment matches the one used for `requirements.txt`
- Update API keys in the appropriate configuration or utility files before running external requests

---

## 🙋‍♂️ Author
Built by the TravelMate team for travel recommendation and conversational AI demos.

