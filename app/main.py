from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import analysis

load_dotenv()

app = FastAPI()

app.include_router(analysis.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Agentic Procurement Analysis API"}
