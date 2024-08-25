from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy.orm import Session
from api.utils.typesense import TypesenseClient
from api.v1.hotels.services import HotelService
from api.v1.hotels import schemas as hotel_schemas
from api.utils import paginator
from api.db.database import get_db
from api.core.dependencies.user import is_authenticated, is_org_member
from api.v1.user import schemas as user_schema
from datetime import datetime, date
from typing import List


app = APIRouter(tags=["Hotels"])

client = TypesenseClient()


@app.post("/hotels", status_code=status.HTTP_201_CREATED, response_model=hotel_schemas.ShowApprovedHotel)
async def add_hotel(
    payload: hotel_schemas.ApprovedHotelBase,
    user: user_schema.ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db)
):
    await is_org_member(organization_id=payload.organization_id, user=user, db=db)

    added_hotel = await HotelService.create(payload=payload, db=db)

    return added_hotel


@app.get("/hotels", status_code=status.HTTP_200_OK)
async def get_hotels(
    organization_id: int,
    country: str = None,
    state: str = None,
    city: str = None,
    page: int = 1,
    size: int = 50,
    user: user_schema.ShowUser = Depends(is_org_member),
    db: Session = Depends(get_db),
):

    page_size = 10 if size < 1 or size > 20 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)

    hotels, total = await HotelService.fetch_all(org_id=organization_id,
                                                 db=db, country=country,
                                                 state=state, city=city,
                                                 size=page_size, offset=offset)

    pointers = paginator.page_urls(
        page=page_number,
        size=page_size,
        count=total,
        endpoint=f'/hotels/{organization_id}',
    )

    response = paginator.build_paginated_response(
        page=page_number,
        size=page_size,
        total=total,
        pointers=pointers,
        items=list(map((lambda hotel: hotel_schemas.ShowApprovedHotel.model_validate(hotel)), hotels)))

    return response


@app.get(
    "/hotels/index",
    status_code=status.HTTP_200_OK,
    response_model=hotel_schemas.HotelResponse
)
async def get_hotels_index(
        organization_id: str,
        search_value: str = '',
        category: str = None,
        location: str = None,
        is_active: bool = True,
        is_approved: bool = None,
        location_type: str = None,
        featured: bool = None,
        type: str = None,
        min_price: int = 0,
        max_price: int = 0,
        facilities: str = None,
        page: int = 1,
        size: int = 50,
        user: user_schema.ShowUser = Depends(is_authenticated),
        db: Session = Depends(get_db),
):
    """
    Desc:
        Fetches all hotels. returns a paginated response with a default size of 50

    Args:
    - organization_id: A unique identifier of an organization
    - search_value (optional): A search string for filtering suppliers to be fetched
    - param reverse_sort (optional): A boolean to determine if objects
        should be sorted in ascending or descending order. defaults to True (ascending order)
    - param user: user authentication validator
    - param page: the page number of items to fetched
    - param size: the number of items to be fetched per page
    - param facilities: A comma separated string of facilities to filter suppliers by
    - param location: The location to retrieve hotels from e.g Lagos
    - param location_type: A string denoting the type of the specified location(city, area, state, country)

    """

    await is_org_member(organization_id=organization_id, user=user, db=db)

    if location and not location_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="location cannot exist without location_type")

    if location_type and not location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="location_type cannot exist without location")

    page_size = 50 if size < 1 or size > 50 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)

    hotels, total_items = await HotelService.fetch_from_index(
        search_value=search_value,
        offset=offset,
        category=category,
        location=location,
        location_type=location_type,
        type=type,
        min_price=min_price,
        max_price=max_price,
        facilities=facilities,
        size=page_size,
        page=page_number,
    )

    hotels = hotel_schemas.IndexResponse.validate_data(value=hotels)

    pointers = paginator.page_urls(
        page=page_number,
        size=page_size,
        count=total_items,
        endpoint='/hotels/index',
    )

    response = paginator.build_paginated_response(
        page=page_number,
        size=page_size,
        total=total_items,
        pointers=pointers,
        items=list(map(lambda hotel: hotel_schemas.ShowHotel(**hotel), hotels))
    )

    return response


@app.get("/hotels/{hotel_id}/rooms", status_code=status.HTTP_200_OK, response_model=List[hotel_schemas.HotelRooms])
async def get_hotel_rooms(
    hotel_id: str,
    organization_id: str,
    start_dt: datetime = None,
    end_dt: datetime = None,
    user: user_schema.ShowUser = Depends(is_org_member),
    db: Session = Depends(get_db),
):
    await is_org_member(organization_id=organization_id, user=user, db=db)

    rooms = await HotelService.fetch_rooms(hotel_id=hotel_id, start_dt=start_dt, end_dt=end_dt)

    print(rooms)

    return rooms
