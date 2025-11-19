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

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal

# Example schemas (you can keep these for reference):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    address: Optional[str] = Field(None, description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# --------------------------------------------------
# Marketplace for tradespeople (plumbers, electricians)
# --------------------------------------------------

TRADES = [
    "plumber",
    "electrician",
]

class Provider(BaseModel):
    """
    Providers (service professionals)
    Collection: "provider"
    """
    name: str = Field(..., description="Business or professional name")
    trade: str = Field(..., description="Type of trade, e.g., plumber or electrician")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    city: Optional[str] = Field(None, description="City or service area")
    description: Optional[str] = Field(None, description="Short bio/summary of services")
    hourly_rate: Optional[float] = Field(None, ge=0, description="Optional hourly rate")
    rating: Optional[float] = Field(4.8, ge=0, le=5, description="Average rating")
    review_count: Optional[int] = Field(0, ge=0, description="Number of reviews")
    badges: Optional[List[str]] = Field(default_factory=list, description="Badges like 'Verified', 'Insured'")

class ServiceRequest(BaseModel):
    """
    Customer job requests
    Collection: "servicerequest"
    """
    name: str = Field(..., description="Customer name")
    email: EmailStr = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone")
    trade: str = Field(..., description="Requested trade: plumber or electrician")
    city: Optional[str] = Field(None, description="Location / city")
    title: str = Field(..., description="Short title for the job")
    details: Optional[str] = Field(None, description="Detailed description of the job")
    budget: Optional[float] = Field(None, ge=0, description="Optional budget")

class Review(BaseModel):
    """
    Reviews for providers
    Collection: "review"
    """
    provider_id: str = Field(..., description="ID of the provider being reviewed")
    name: str = Field(..., description="Reviewer name")
    rating: int = Field(..., ge=1, le=5, description="Star rating 1-5")
    comment: Optional[str] = Field(None, description="Optional review comment")

# ------------------------
# Auth payload schemas
# ------------------------

Role = Literal["provider", "requester"]

class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Role

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class AuthUser(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role

class AuthResponse(BaseModel):
    token: str
    user: AuthUser

# Note: The Flames database viewer can read these schemas from GET /schema
# No in-memory storage is used; MongoDB handles persistence.
