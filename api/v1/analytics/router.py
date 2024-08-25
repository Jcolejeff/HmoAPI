from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from api.db.database import get_db
from api.core.dependencies.user import is_authenticated
from api.v1.user.schemas import ShowUser
from api.v1.analytics.services import AnalyticsService
from api.v1.analytics import schemas as analytics_schemas

from sqlalchemy.orm import Session

app = APIRouter(tags=["Analytics"])

@app.get('/analytics')
async def get_analytics(
        organization_id: int,
        start_date: date = None,
        end_date: date = None,
        user: ShowUser = Depends(is_authenticated),
        db: Session = Depends(get_db)
):
    """
        Returns organization analytics

        `bookings_count_range` should be from and to dates with seperate with commas. For example: 2024-04-01, 2024-05-01
    """
    analytics_service = AnalyticsService(organization_id=organization_id, db=db, start_dt=start_date, end_dt=end_date)
    departments_count = analytics_service.get_department_count_in_organization()
    users_count = analytics_service.get_users_count_in_organization()
    total_hotels_booked = analytics_service.get_total_hotels_booked()
    total_organizational_spend = analytics_service.get_total_spend()
    total_spend_per_department = analytics_service.get_total_spend_per_department()
    total_bookings_count = analytics_service.get_total_bookings()

    return {
        "departments_count": departments_count,
        "users_count": users_count,
        "total_hotels_booked": total_hotels_booked,
        "total_organization_spend": total_organizational_spend,
        "total_spend_per_department": total_spend_per_department,
        "total_bookings_count": total_bookings_count,
    }

@app.get('/analytics/top-travellers',
         response_model= list[analytics_schemas.TopTravellersResponse]
         )
async def get_top_travellers(
        organization_id: int,
        start_date: date = None,
        end_date: date = None,
        user: ShowUser = Depends(is_authenticated),
        db: Session = Depends(get_db)
):
    """
        Returns details of the top travellers in an organization.

    """
    analytics_service = AnalyticsService(organization_id=organization_id, db=db, start_dt=start_date, end_dt=end_date)
    top_travellers = analytics_service.get_top_travellers()

    return top_travellers


@app.get('/analytics/top-hotels',
         response_model=list[analytics_schemas.TopHotelsResponse]
         )
async def get_top_hotels(
        organization_id: int,
        start_date: date = None,
        end_date: date = None,
        user: ShowUser = Depends(is_authenticated),
        db: Session = Depends(get_db)
):
    """
        Returns details of the top Hotels in an organization.

    """
    analytics_service = AnalyticsService(organization_id=organization_id, db=db, start_dt=start_date, end_dt=end_date)
    top_hotels= analytics_service.get_top_hotels()

    return top_hotels


@app.get('/analytics/top-destinations',
         response_model=list[analytics_schemas.TopDestinationsResponse]
         )
async def get_top_destinations(
        organization_id: int,
        start_date: date = None,
        end_date: date = None,
        user: ShowUser = Depends(is_authenticated),
        db: Session = Depends(get_db)
):
    """
        Returns details of the top destinations in an organization.

    """
    analytics_service = AnalyticsService(organization_id=organization_id, db=db, start_dt=start_date, end_dt=end_date)
    top_destinations = analytics_service.get_top_destinations()


    return top_destinations


@app.get('/analytics/coworkers',
         response_model= list[analytics_schemas.CoworkersResponse]
         )
async def get_coworkers(
        organization_id: int,
        start_date: date = None,
        end_date: date = None,
        user: ShowUser = Depends(is_authenticated),
        db: Session = Depends(get_db)
):
    """
        Returns details of the coworkers in an organization.

    """
    analytics_service = AnalyticsService(organization_id=organization_id, db=db, start_dt=start_date, end_dt=end_date)
    coworkers = analytics_service.get_coworkers()


    return coworkers

@app.post('/analytics/reports'
         )
async def generate_reports(
        body: analytics_schemas.CreateReport,
        background_task: BackgroundTasks,
        user: ShowUser = Depends(is_authenticated),
        db: Session = Depends(get_db)
):
    """
        Generate reports based on specific parameters in an organization.

    """
    
    analytics_service = AnalyticsService(
        organization_id=body.organization_id, 
        db=db, 
        start_dt=body.start_date, 
        end_dt=body.end_date
    )

    background_task.add_task(analytics_service.generate_reports, body, background_task) 

    return "Report is being generated"