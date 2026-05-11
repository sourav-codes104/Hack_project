import os
from dotenv import load_dotenv

load_dotenv()

print("FILE EXISTS:", os.path.exists(".env"))
print("VALUE:", os.getenv("GEMINI_API_KEY"))