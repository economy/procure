from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

API_KEY = os.getenv("API_KEY")


@app.get("/")
def read_root():
    return {"Hello": "World"}
