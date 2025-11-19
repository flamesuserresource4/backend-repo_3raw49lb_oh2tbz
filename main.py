import os
import base64
import json
import hmac
import hashlib
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from schemas import Provider, ServiceRequest, Review, RegisterInput, LoginInput, AuthUser, AuthResponse

app = FastAPI(title="Trades Marketplace API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
TOKEN_EXP_SECONDS = 60 * 60 * 24 * 7  # 7 days


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(data: str) -> str:
    return _b64url(hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).digest())


def create_token(user: AuthUser) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "exp": int(time.time()) + TOKEN_EXP_SECONDS,
    }
    h = _b64url(json.dumps(header).encode())
    p = _b64url(json.dumps(payload).encode())
    s = _sign(f"{h}.{p}")
    return f"{h}.{p}.{s}"


def verify_token(token: str) -> Optional[AuthUser]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h, p, s = parts
        if _sign(f"{h}.{p}") != s:
            return None
        payload = json.loads(base64.urlsafe_b64decode(p + "==").decode())
        if payload.get("exp", 0) < time.time():
            return None
        return AuthUser(id=payload["id"], name=payload["name"], email=payload["email"], role=payload["role"]) 
    except Exception:
        return None


def hash_password(password: str, salt: Optional[str] = None):
    if salt is None:
        salt_bytes = os.urandom(16)
        salt = base64.b64encode(salt_bytes).decode()
    else:
        # ensure provided salt is string
        if isinstance(salt, bytes):
            salt = base64.b64encode(salt).decode()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), 100_000)
    return base64.b64encode(dk).decode(), salt


@app.get("/")
def read_root():
    return {"message": "Trades Marketplace API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# -------------------------------
# Auth
# -------------------------------

@app.post("/auth/register", response_model=AuthResponse)
def register(payload: RegisterInput):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    existing = db["account"].find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    pwd_hash, salt = hash_password(payload.password)
    doc = {
        "name": payload.name,
        "email": payload.email,
        "role": payload.role,
        "password_hash": pwd_hash,
        "salt": salt,
    }
    res = db["account"].insert_one(doc)
    user = AuthUser(id=str(res.inserted_id), name=payload.name, email=payload.email, role=payload.role)
    token = create_token(user)
    return AuthResponse(token=token, user=user)


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginInput):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    acc = db["account"].find_one({"email": payload.email})
    if not acc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    calc_hash, _ = hash_password(payload.password, salt=acc.get("salt"))
    if calc_hash != acc.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = AuthUser(id=str(acc.get("_id")), name=acc.get("name"), email=acc.get("email"), role=acc.get("role"))
    token = create_token(user)
    return AuthResponse(token=token, user=user)


@app.get("/me")
def me(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.replace("Bearer ", "").strip()
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

# -------------------------------
# Providers
# -------------------------------

@app.get("/providers")
def list_providers(trade: Optional[str] = None, city: Optional[str] = None, limit: int = 20):
    if db is None:
        return []
    filt = {}
    if trade:
        filt["trade"] = trade
    if city:
        filt["city"] = city
    return get_documents("provider", filt, limit)


@app.post("/providers")
def create_provider(provider: Provider):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    provider_id = create_document("provider", provider)
    return {"id": provider_id}

# -------------------------------
# Service Requests
# -------------------------------

@app.post("/requests")
def create_request(request: ServiceRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    request_id = create_document("servicerequest", request)
    return {"id": request_id}

# -------------------------------
# Reviews
# -------------------------------

@app.post("/reviews")
def create_review(review: Review):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    review_id = create_document("review", review)
    return {"id": review_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
