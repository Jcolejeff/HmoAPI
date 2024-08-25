from pydantic import BaseModel, field_validator
from datetime import datetime, date
from api.v1.user.schemas import ShowUser
from typing import List, Any, Optional


class ApprovedHotelBase(BaseModel):
    organization_id: int
    hotel_name: str
    state: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class ShowApprovedHotel(ApprovedHotelBase):
    id: int
    is_deleted: bool
    date_created: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


class ShowHotel(BaseModel):
    business_name: str
    categories: Optional[list] = None
    city_facet: Optional[list] = None
    contact_infos: Optional[list] = None
    country_facet: Optional[list] = None
    default_currency_code: Optional[str] = None
    driving_instructions: Optional[str] = None
    extra_infos: Optional[list] = None
    facilities: Optional[dict] = None
    featured_reviews: Optional[list] = []
    geo_location: Optional[list] = []
    id: Optional[str]
    is_active: bool = True
    is_deleted: bool = False
    LGA_facet: Optional[list] = []
    location_obj: Optional[dict] = {}
    locations: Optional[List] = []
    maxprice: Optional[float] = 0.0
    minprice: Optional[float] = 0.0
    organization_id: Optional[str]
    photos: Optional[List] = []
    ranking5: Optional[int] = 0
    ranking6: Optional[int] = 0
    rating_avg: Optional[float] = 0.0
    reviews_count: Optional[int] = 0
    state_facet: Optional[list] = []
    status: Optional[str] = None
    street_facet: Optional[list] = []
    total_products: Optional[int] = 0
    unique_id: Optional[str]
    unique_url_slug: Optional[str]
    url: Optional[str] = None
    user_id: Optional[str] = None


class HotelResponse(BaseModel):
    page: int
    size: int
    total: int
    previous_page: Optional[str]
    next_page: Optional[str]
    items: List[ShowHotel]


class IndexResponse(BaseModel):
    hotels: List[dict]

    @field_validator('hotels')
    @classmethod
    def validate_data(cls, value: list):
        hotels = [sup['document'] for sup in value]

        return hotels


class HotelRooms(BaseModel):
    name: str
    current_price: float | None

    class Config:
        from_attributes = True
