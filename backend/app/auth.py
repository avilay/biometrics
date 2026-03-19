import time
from typing import Optional

import httpx
import jwt
from cryptography.x509 import load_pem_x509_certificate
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.database import get_db

DEMO_FIREBASE_UID = "demo-user"
DEMO_TOKEN = "demo"

GOOGLE_CERTS_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/"
    "securetoken@system.gserviceaccount.com"
)

_cached_keys: dict[str, str] = {}
_cache_expiry: float = 0.0

security = HTTPBearer()


async def _fetch_google_public_keys() -> dict[str, str]:
    global _cached_keys, _cache_expiry
    now = time.time()
    if _cached_keys and now < _cache_expiry:
        return _cached_keys

    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_CERTS_URL)
        resp.raise_for_status()
        _cached_keys = resp.json()
        # Parse max-age from Cache-Control header
        cache_control = resp.headers.get("Cache-Control", "")
        max_age = 3600  # default 1 hour
        for part in cache_control.split(","):
            part = part.strip()
            if part.startswith("max-age="):
                try:
                    max_age = int(part.split("=")[1])
                except ValueError:
                    pass
        _cache_expiry = now + max_age
    return _cached_keys


async def verify_firebase_token(token: str) -> dict:
    keys = await _fetch_google_public_keys()

    # Decode header to find the key id
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.exceptions.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )

    kid = unverified_header.get("kid")
    if not kid or kid not in keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token key ID not found in Google public keys",
        )

    cert_str = keys[kid]
    cert = load_pem_x509_certificate(cert_str.encode("utf-8"))
    public_key = cert.public_key()

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.FIREBASE_PROJECT_ID,
            issuer=f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}"
        )

    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials

    # Demo user shortcut
    if token == DEMO_TOKEN:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, firebase_uid, email, display_name FROM users WHERE firebase_uid = ?",
                (DEMO_FIREBASE_UID,),
            )
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "firebase_uid": row["firebase_uid"],
                    "email": row["email"],
                    "display_name": row["display_name"],
                    "is_demo": True,
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Demo user not found. Please seed the database first.",
                )

    payload = await verify_firebase_token(token)

    firebase_uid = payload.get("uid") or payload.get("user_id") or payload.get("sub")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier",
        )

    email = payload.get("email")
    display_name = payload.get("name") or payload.get("display_name")

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, firebase_uid, email, display_name FROM users WHERE firebase_uid = ?",
            (firebase_uid,),
        )
        row = await cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "firebase_uid": row["firebase_uid"],
                "email": row["email"],
                "display_name": row["display_name"],
                "is_demo": False,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found. Please log in first.",
            )


def require_write(user: dict = Depends(get_current_user)) -> dict:
    if user.get("is_demo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo users cannot modify data",
        )
    return user
