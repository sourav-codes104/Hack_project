# AI TravelMate

AI TravelMate is a Flask-based travel planning web app that helps users discover destinations, generate trip recommendations, build itineraries, chat with an AI travel assistant, and save trip history. It combines a traditional web application with Gemini-powered AI, local recommendation data, weather integration, user authentication, and an admin dashboard.

Live deployment: [https://travelmate-6zk9.onrender.com](https://travelmate-6zk9.onrender.com)

## Features

- User signup, signin, logout, and session-based dashboards
- Optional Google OAuth login
- AI travel chat powered by Google Gemini
- Destination recommendations based on location, interest, budget, travel mode, duration, place type, season, and travel dates
- "Show more" recommendations without repeating already displayed places
- Detailed day-wise itinerary generation
- Weather lookup for selected locations
- Trip save and trip history pages for logged-in users
- Admin login and dashboard for user, destination, feedback, and database management
- Feedback form with admin export support
- SQLite database initialization and persistence for local development
- Render deployment configuration with Gunicorn

## Tech Stack

- Backend: Python, Flask, Gunicorn
- Frontend: HTML, CSS, JavaScript, Jinja templates
- AI: Google Gemini API, spaCy NLP, local ML recommendation helpers
- Auth: Flask sessions, Authlib Google OAuth
- Database: SQLite
- Data: JSON and CSV travel datasets
- Deployment: Render Web Service

## Project Structure

```text
Hack_project/
├── app.py                     # Flask app entry point and route definitions
├── render.yaml                # Render Blueprint configuration
├── Procfile                   # Gunicorn process command
├── requirements.txt           # Python dependencies
├── .python-version            # Python version used on Render
├── data/
│   ├── destinations.json      # Local destination metadata
│   ├── training_data.csv      # Training data for recommendation logic
│   └── travel_context.txt     # Context used by chatbot logic
├── database/
│   ├── users_export.csv       # Admin export output
│   └── feedback_export.csv    # Admin export output
├── model/
│   ├── classes.py             # User, destination, travel plan, admin classes
│   ├── conversational_ai.py   # Gemini conversational assistant
│   ├── recommender.py         # Recommendation and itinerary generation
│   ├── ml_recommender.py      # Local ML/template recommendation fallback
│   ├── trained_recommender.py # Trained recommender helper
│   ├── ner_utils.py           # Named entity/location extraction
│   └── *.pkl                  # Trained model/vectorizer files
├── static/
│   ├── css/                   # Styles and image assets
│   ├── images/                # App imagery
│   └── javascript/            # Frontend scripts
├── templates/                 # Jinja HTML templates
└── utils/
    ├── database_setup.py      # SQLite schema setup and feedback persistence
    ├── weather_app.py         # Weather helper
    ├── maps_api.py            # Map-related helper
    └── text_to_speech.py      # Text-to-speech helper
```

## Main Routes

| Route | Purpose |
| --- | --- |
| `/` | Landing page |
| `/user_auth` | User authentication page |
| `/signup` | Create a user account |
| `/signin` | User/admin login |
| `/auth/google` | Start Google OAuth login |
| `/auth/google/callback` | Google OAuth callback |
| `/user` | User dashboard |
| `/ai_chat` | AI chat endpoint |
| `/recommend` | Generate destination recommendations |
| `/recommend/more` | Fetch more recommendations |
| `/itinerary` | Generate detailed itinerary |
| `/save-trip` | Save a trip to history |
| `/history` | View saved trip history |
| `/api/history` | Trip history JSON API |
| `/api/history/delete` | Delete a saved trip |
| `/admin` | Admin login |
| `/admin/dashboard` | Admin dashboard |
| `/admin/manage_db/<action>` | Admin database utilities |
| `/admin/export_feedback` | Export feedback CSV |
| `/feedback` | Submit feedback |
| `/test` | Health check route |

## Environment Variables

Create a `.env` file for local development. Do not commit this file.

```env
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
SECRET_KEY=replace_with_a_long_random_secret
FLASK_DEBUG=false
```

Notes:

- `GEMINI_API_KEY` is required for AI chat and Gemini fallback recommendation features.
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are required only for Google sign-in.
- `SECRET_KEY` should be set in production so Flask sessions remain secure.
- The app can boot without Gemini or Google OAuth values, but related features will be unavailable or degraded.

## Local Setup

```bash
git clone https://github.com/sourav-codes104/Hack_project.git
cd Hack_project
python -m venv myenv
```

Activate the virtual environment on Windows PowerShell:

```powershell
.\myenv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

Open the local site:

```text
http://127.0.0.1:5000
```

Health check:

```text
http://127.0.0.1:5000/test
```

## Database

The app uses SQLite. On startup, `utils/database_setup.py` creates the required tables if they do not already exist.

Main tables:

- `User`
- `Destination`
- `Accommodation`
- `TravelPlan`
- `Booking`
- `feedback`

Local database file:

```text
database/travel.db
```

This database file is ignored for deployment. Render free instances have an ephemeral filesystem, so production data stored in SQLite may not persist permanently across restarts or redeploys. For long-term production use, migrate the app to a managed database such as Render Postgres.

## Render Deployment

This repository includes a `render.yaml` Blueprint for deployment.

Current live service:

[https://travelmate-6zk9.onrender.com](https://travelmate-6zk9.onrender.com)

Render configuration:

- Runtime: Python
- Plan: Free
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --workers 1 --threads 2 --timeout 120`
- Health check path: `/test`
- Python version: `3.11`

Required Render environment variables:

```text
GEMINI_API_KEY
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
SECRET_KEY
```

Deployment steps:

1. Push the project to GitHub.
2. Open [Render Blueprints](https://dashboard.render.com/blueprints) or create a new web service from the repository.
3. Connect `sourav-codes104/Hack_project`.
4. Use the included `render.yaml` or manually set the same build/start commands.
5. Add the required environment variables in Render.
6. Deploy the latest commit.

Free instance note:

Render free services can spin down after inactivity. The first request after a spin-down can take 50 seconds or more. The project also avoids loading heavy AI/ML modules during startup so it can fit better within the free instance memory limit.

## Admin Access

The current code contains a hardcoded admin login:

```text
Username: Sourav
Password: 12345
```

For production, move admin credentials into environment variables and use hashed passwords before sharing the app publicly.

## Security Notes

- Do not commit `.env`, API keys, OAuth secrets, or database files.
- Replace hardcoded admin credentials before production use.
- Use a strong `SECRET_KEY` in Render.
- SQLite is suitable for demos and local development, but a managed production database is recommended.
- OAuth redirect URLs must be configured in Google Cloud Console for both local and Render domains.

## Known Limitations

- Render free instances have limited memory and spin down with inactivity.
- SQLite data on Render free hosting may not persist across deploys/restarts.
- Some AI features require a valid Gemini API key.
- Google sign-in requires correctly configured OAuth credentials and redirect URLs.

## Author

Built by Sourav Singh as an AI-powered travel recommendation and itinerary planning project.
