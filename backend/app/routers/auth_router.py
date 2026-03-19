from fastapi import APIRouter, HTTPException, status

from app.auth import verify_firebase_token, DEMO_FIREBASE_UID
from app.database import get_db
from app.models import LoginRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse)
async def login(body: LoginRequest):
    payload = await verify_firebase_token(body.id_token)

    firebase_uid = payload.get("uid") or payload.get("user_id") or payload.get("sub")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier",
        )

    email = payload.get("email")
    display_name = payload.get("name") or payload.get("display_name")

    async with get_db() as db:
        # Upsert: try insert, on conflict update
        await db.execute(
            """
            INSERT INTO users (firebase_uid, email, display_name)
            VALUES (?, ?, ?)
            ON CONFLICT(firebase_uid) DO UPDATE SET
                email = excluded.email,
                display_name = excluded.display_name
            """,
            (firebase_uid, email, display_name),
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT id, email, display_name FROM users WHERE firebase_uid = ?",
            (firebase_uid,),
        )
        user = await cursor.fetchone()

    return UserResponse(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
    )


@router.post("/demo-login", response_model=UserResponse)
async def demo_login():
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, email, display_name FROM users WHERE firebase_uid = ?",
            (DEMO_FIREBASE_UID,),
        )
        user = await cursor.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo user not found. Please seed the database first.",
        )

    return UserResponse(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
    )
