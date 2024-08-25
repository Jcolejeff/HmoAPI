from fastapi import status
from decouple import config
import requests
from api.core.base.services import Service
from fastapi import HTTPException
from api.utils.typesense import TypesenseClient
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_
from api.v1.hotels.models import ApprovedHotel
from api.v1.hotels.schemas import ApprovedHotelBase
from datetime import datetime, date

client = TypesenseClient()
API_URL = config("TIMBU_API")
HNG_ORG_ID = config('HNG_ORG_ID')
API_KEY = config("API_KEY")
APP_ID = config("APP_ID")


class HotelService():
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    async def fetch_from_index(
        cls,
        search_value: str,
        offset: int,
        page: int = 1,
        category: str = None,
        location: str = None,
        location_type: str = None,
        type: str = None,
        min_price: int = 0,
        max_price: int = 0,
        facilities: str = None,
        size: int = 50,
    ):

        organization_id = config("HNG_ORG_ID")

        query = "*"
        query_by = "business_name"
        filter_by = f"is_deleted:= false && is_approved:= true"
        sort_by = f"ranking5: desc, sales_count:desc"

        if search_value:
            query = f"{search_value}"
            query_by = f"{query_by}, location_obj.city, location_obj.state"

        if organization_id:
            filter_by = f"{filter_by} && organization_id := {organization_id}"

        if category:
            if category == "cheap":
                sort_by = 'minprice:asc, rating_avg:desc, sales_count:desc'
                filter_by = f"{filter_by} && minprice:>1 && num_of_images:>= 4"

            elif category == "popular":
                sort_by = '_eval(is_active:true):desc, reviews_count:desc'

            elif category == "best":
                sort_by = 'rating_avg:desc, sales_count:desc'
                filter_by = f"{filter_by} && minprice:>1 && num_of_images:>= 4 && is_active:=true && reviews_count:>2"

            elif category == "luxury":
                sort_by = 'minprice:desc, rating_avg:desc, sales_count:desc'
                filter_by = f"{filter_by} && minprice:>1 && num_of_images:>= 4 && is_active:=true"

        if type:
            filter_by = f"{filter_by} && categories : {type}"

        if min_price and max_price:
            filter_by = f"{filter_by} && minprice: [{min_price}..{max_price}]"

        if facilities:
            facilities = facilities.split(',')
            filter_by = f"{filter_by} && {' && '.join(map(lambda x: 'facilities.' + x.strip() + ':= true', facilities))}"

        if location:
            if not location_type:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="location cannot exist without location_type")

            filter_by = f"{filter_by} && location_obj.{location_type} := {location}"

        params = {
            'q': query,
            'query_by': query_by,
            'filter_by': filter_by,
            'sort_by': sort_by,
            'page': page,
            'offset': offset,
            'per_page': size
        }

        suppliers = []
        try:
            res = client.collections['suppliers'].documents.search(params)
            total_items = res['found']
            suppliers = res['hits']

        except Exception as ex:
            print(ex)
            pass

        if not suppliers:
            return ([], 0)

        return (suppliers, total_items)

    @classmethod
    async def create(cls, payload: ApprovedHotelBase, db: Session):
        approved_hotel = ApprovedHotel(**payload.dict())
        db.add(approved_hotel)

        db.commit()

        return approved_hotel

    @classmethod
    async def fetch_all(cls, org_id: int, db: Session, country: str = None, state: str = None, city: str = None, size: int = 50, offset: int = 50):

        base_query = db.query(ApprovedHotel).filter(
            and_(ApprovedHotel.organization_id == org_id, ApprovedHotel.is_deleted == False))

        if country:
            base_query = base_query.filter(ApprovedHotel.country == country)
        if state:
            base_query = base_query.filter(ApprovedHotel.state == state)
        if city:
            base_query = base_query.filter(ApprovedHotel.city == city)

        total = base_query.count()
        hotels = base_query.limit(limit=size).offset(offset=offset).all()

        return hotels, total

    @classmethod
    async def fetch_rooms(cls, hotel_id: str, start_dt: datetime = None, end_dt: datetime = None):
        rooms = requests.get(f'{API_URL}/products', params={
            "supplier_id": hotel_id,
            "organization_id": HNG_ORG_ID,
            "currency_code": "NGN",
            "is_available": True,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "Apikey": API_KEY,
            "Appid": APP_ID
        },)

        return rooms.json()["items"]
