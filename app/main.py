from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import analysis

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Set up CORS
origins = [
    "http://localhost:5173",  # Vite default dev server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(analysis.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Agentic Procurement Analysis API"}
