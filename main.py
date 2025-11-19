import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from schemas import Provider, ServiceRequest, Review

app = FastAPI(title="Trades Marketplace API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
