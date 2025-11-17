"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# -------- Platform Schemas ---------

class Company(BaseModel):
    """
    Companies participating in tenders
    Collection name: "company"
    """
    name: str = Field(..., description="Company legal name")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    address: Optional[str] = Field(None, description="Registered address")
    country: str = Field("Qatar", description="Country")

class Tender(BaseModel):
    """
    Tender listings
    Collection name: "tender"
    """
    title: str = Field(..., description="Tender title")
    description: str = Field(..., description="Detailed description")
    category: str = Field(..., description="Category e.g. Construction, IT, Services")
    budget_qar: Optional[float] = Field(None, ge=0, description="Estimated budget in QAR")
    issuer: str = Field(..., description="Issuing organization")
    location: str = Field("Qatar", description="Project location")
    deadline: datetime = Field(..., description="Submission deadline (ISO 8601)")
    status: str = Field("open", description="open | closed | awarded")
    tags: Optional[List[str]] = Field(default_factory=list, description="Search tags")

class Bid(BaseModel):
    """
    Bids submitted to tenders
    Collection name: "bid"
    """
    tender_id: str = Field(..., description="Reference to tender _id as string")
    company_name: str = Field(..., description="Submitting company name")
    contact_email: Optional[str] = Field(None, description="Contact email")
    amount_qar: float = Field(..., ge=0, description="Bid amount in QAR")
    proposal_summary: Optional[str] = Field(None, description="Short summary")
    delivery_time_days: Optional[int] = Field(None, ge=0, description="Delivery timeline in days")

# Example schemas kept for reference
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
