import sys
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import analysis

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

print(os.getenv("GOOGLE_API_KEY"))

app.include_router(analysis.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Agentic Procurement Analysis API"}
