from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class IngredientsOutputFormat(BaseModel):
    ingredients: List[str]
    amounts: List[str]
    language: str

class OtherInfoOutputFormat(BaseModel):
    product_name: str
    brand: str
    net_content: str
    manufacturing_date: str
    expiry_date: str
    country_of_origin: str
    manufacturer: str
    usage_instructions: str
    storage_instructions: str
    nutritional_info: str


class TranslateRequest(BaseModel):
    info: Dict[str, Any]
    language: str

# dict 
# nutritional_info: 