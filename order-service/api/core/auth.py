from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from api.core.config import settings

bearer_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    print(token)
    print(settings.SECRET_KEY)
    try:
        # TURN ON THE VERIFY AUD !!!!!!!!!!!
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"], options={"verify_aud": False})
        print("Decoded payload:", payload)
        return payload
    except JWTError as e:
        print("JWT Error:", e)
        raise HTTPException(status_code=401, detail="Invalid token")
