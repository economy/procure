from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import os

API_KEY = os.getenv("API_KEY") # Use the general API_KEY for server auth
API_KEY_NAME = "x-api-key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        ) 