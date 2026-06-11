from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    source: str
    out_of_context: bool
    details: Optional[dict] = None


class Product(BaseModel):
    id: int
    name: str
    description: str
    quantity: int
    price: float
    category: str
    color: str
    size: str
    material: str
    sku: str
