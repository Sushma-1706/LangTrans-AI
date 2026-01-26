import os
from dotenv import load_dotenv

load_dotenv()

# Change this to look for GROQ_API_KEY
GROQ_API_KEY = os.getenv("GROQ_API_KEY")