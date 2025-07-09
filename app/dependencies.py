from fastapi import Header, HTTPException, status
import os

async def get_api_key(x_api_key: str = Header(...)):
    """
    Dependency to verify the X-API-Key header.
    """
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return x_api_key 