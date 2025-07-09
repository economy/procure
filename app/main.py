from fastapi import FastAPI, Depends
from dotenv import load_dotenv
import os
from .dependencies import get_api_key

load_dotenv()

app = FastAPI()


@app.get("/")
def read_root(api_key: str = Depends(get_api_key)):
    return {"Hello": "Authenticated World"}
