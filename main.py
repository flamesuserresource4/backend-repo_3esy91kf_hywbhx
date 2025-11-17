import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from bson import ObjectId
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Tender, Bid, Company

app = FastAPI(title="Qatar Tenders API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TenderOut(BaseModel):
    id: str
    title: str
    description: str
    category: str
    budget_qar: Optional[float] = None
    issuer: str
    location: str
    deadline: datetime
    status: str
    tags: Optional[List[str]] = []

class BidOut(BaseModel):
    id: str
    tender_id: str
    company_name: str
    contact_email: Optional[str] = None
    amount_qar: float
    proposal_summary: Optional[str] = None
    delivery_time_days: Optional[int] = None

@app.get("/")
def read_root():
    return {"message": "Qatar Tender Platform Backend Running"}

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

# -------- Tenders Endpoints --------

@app.post("/api/tenders", response_model=Dict[str, str])
async def create_tender(tender: Tender):
    try:
        tender_id = create_document("tender", tender)
        return {"id": tender_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tenders", response_model=List[TenderOut])
async def list_tenders(q: Optional[str] = None, category: Optional[str] = None, status: Optional[str] = None):
    try:
        filter_dict = {}
        if q:
            filter_dict["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
                {"tags": {"$regex": q, "$options": "i"}},
            ]
        if category:
            filter_dict["category"] = category
        if status:
            filter_dict["status"] = status

        docs = get_documents("tender", filter_dict)
        results: List[TenderOut] = []
        for d in docs:
            results.append(TenderOut(
                id=str(d.get("_id")),
                title=d.get("title"),
                description=d.get("description"),
                category=d.get("category"),
                budget_qar=d.get("budget_qar"),
                issuer=d.get("issuer"),
                location=d.get("location"),
                deadline=d.get("deadline"),
                status=d.get("status", "open"),
                tags=d.get("tags", []),
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tenders/{tender_id}", response_model=TenderOut)
async def get_tender(tender_id: str):
    try:
        from bson.objectid import ObjectId
        doc = db["tender"].find_one({"_id": ObjectId(tender_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tender not found")
        return TenderOut(
            id=str(doc.get("_id")),
            title=doc.get("title"),
            description=doc.get("description"),
            category=doc.get("category"),
            budget_qar=doc.get("budget_qar"),
            issuer=doc.get("issuer"),
            location=doc.get("location"),
            deadline=doc.get("deadline"),
            status=doc.get("status", "open"),
            tags=doc.get("tags", []),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Bids Endpoints --------

@app.post("/api/tenders/{tender_id}/bids", response_model=Dict[str, str])
async def submit_bid(tender_id: str, bid: Bid):
    try:
        # ensure tender exists
        from bson.objectid import ObjectId
        if not db["tender"].find_one({"_id": ObjectId(tender_id)}):
            raise HTTPException(status_code=404, detail="Tender not found")
        data = bid.model_dump()
        data["tender_id"] = tender_id
        bid_id = create_document("bid", data)
        return {"id": bid_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tenders/{tender_id}/bids", response_model=List[BidOut])
async def list_bids(tender_id: str):
    try:
        docs = get_documents("bid", {"tender_id": tender_id})
        results: List[BidOut] = []
        for d in docs:
            results.append(BidOut(
                id=str(d.get("_id")),
                tender_id=d.get("tender_id"),
                company_name=d.get("company_name"),
                contact_email=d.get("contact_email"),
                amount_qar=d.get("amount_qar"),
                proposal_summary=d.get("proposal_summary"),
                delivery_time_days=d.get("delivery_time_days"),
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Seed sample tenders for demo --------

@app.post("/api/seed", response_model=dict)
async def seed_sample():
    try:
        examples = [
            {
                "title": "Road Maintenance for Al Rayyan",
                "description": "Annual maintenance of municipal roads including resurfacing and signage.",
                "category": "Construction",
                "budget_qar": 2500000,
                "issuer": "Ministry of Municipality",
                "location": "Al Rayyan, Qatar",
                "deadline": datetime.utcnow(),
                "status": "open",
                "tags": ["roads", "maintenance", "municipality"]
            },
            {
                "title": "IT Infrastructure Upgrade - Education Sector",
                "description": "Supply and installation of network equipment and servers for public schools.",
                "category": "IT",
                "budget_qar": 1800000,
                "issuer": "Ministry of Education and Higher Education",
                "location": "Doha, Qatar",
                "deadline": datetime.utcnow(),
                "status": "open",
                "tags": ["network", "servers", "education"]
            },
            {
                "title": "Healthcare Consumables Supply",
                "description": "Framework agreement for supply of medical consumables to hospitals.",
                "category": "Healthcare",
                "budget_qar": 1200000,
                "issuer": "Ministry of Public Health",
                "location": "Qatar",
                "deadline": datetime.utcnow(),
                "status": "open",
                "tags": ["medical", "consumables", "framework"]
            }
        ]
        created = 0
        for ex in examples:
            create_document("tender", ex)
            created += 1
        return {"inserted": created}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
