import os
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, text
from pprint import pprint
from fpdf import FPDF

from api.v1.groups.models import Group, GroupMember
from api.v1.organization.models import OrganizationUser
from api.v1.requests.models import Request, RequestStatusEnum
from api.v1.user.models import User
from api.v1.analytics import schemas as analytics_schemas
from api.v1.emails.services import EmailService

from api.utils.sql import sql_count

class AnalyticsService:
    def __init__(self, organization_id: int, db: Session, start_dt: date = None, end_dt: date = None) -> None:
        self.organization_id = organization_id
        self.db = db
        self.start_dt = start_dt
        self.end_dt = end_dt
    
    def get_department_count_in_organization(self):
        """
            Returns the number of departments in an organization
        """
        dept_count_query = (
            self.db.query(func.count(Group.id))
            .filter(
                Group.organization_id == self.organization_id,
                Group.is_deleted == False
            )
        )

        if self.start_dt:
            dept_count_query = dept_count_query.filter(Group.date_created >= self.start_dt)
        
        if self.end_dt:
            dept_count_query = dept_count_query.filter(Group.date_created <= self.end_dt)

        dept_count: int = dept_count_query.scalar()
        
        return dept_count

    def get_users_count_in_organization(self):
        users_count_query = (
            self.db.query(func.count(OrganizationUser.id))
            .filter(
                OrganizationUser.organization_id == self.organization_id,
                OrganizationUser.is_deleted == False,
            )
        )

        if self.start_dt:
            users_count_query = users_count_query.filter(OrganizationUser.created_at >= self.start_dt)
        
        if self.end_dt:
            users_count_query = users_count_query.filter(OrganizationUser.created_at <= self.end_dt)

        users_count: int = users_count_query.scalar()

        return users_count

    def get_total_hotels_booked(self):
        total_hotels_booked_query = (
            self.db.query(func.count(Request.hotel.distinct()))
            .filter(
                Request.organization_id == self.organization_id, 
                Request.is_deleted == False,
            )
        )

        if self.start_dt:
            total_hotels_booked_query = total_hotels_booked_query.filter(Request.date_created >= self.start_dt)
        
        if self.end_dt:
            total_hotels_booked_query = total_hotels_booked_query.filter(Request.date_created <= self.end_dt)
        
        total_hotels_booked = total_hotels_booked_query.scalar()
        return total_hotels_booked
    
    def get_total_spend(self):
        total_spend_query = (
            self.db.query(func.sum(func.datediff(Request.end, Request.start) * Request.rate))
            .filter(
                Request.organization_id == self.organization_id,
                Request.is_deleted == False,
            )
        )

        if self.start_dt:
            total_spend_query = total_spend_query.filter(Request.date_created >= self.start_dt)
        
        if self.end_dt:
            total_spend_query = total_spend_query.filter(Request.date_created <= self.end_dt)
        
        total_spend: int = total_spend_query.scalar()

        return total_spend

    
    def get_total_spend_per_department(self):
        query = text(
            f"""SELECT `groups`.name AS groups_name, ( 
                SELECT sum(`r`.rate * DATEDIFF(`r`.end, `r`.start)) AS sum_1 FROM requests as r
                INNER JOIN group_members ON group_members.group_id = `groups`.id 
                WHERE `r`.requester_id = group_members.member_id 
                AND `groups`.organization_id = {self.organization_id} 
                AND `groups`.is_deleted = false
                AND `r`.is_deleted = false
                {'AND DATE(`r`.date_created) >=' if self.start_dt else ''} {f"'{str(self.start_dt)}'" if self.start_dt else ''}
                {'AND DATE(`r`.date_created) <=' if self.end_dt else ''} {f"'{str(self.end_dt)}'" if self.end_dt else ''}
                ) as sum
            FROM `groups` 
            WHERE `groups`.organization_id = {self.organization_id} 
            AND `groups`.is_deleted = "false"
            """)

        print(query)

        self.db.execute(text("SET sql_mode = (SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''))"))

        total_spends_per_dept_result_set = self.db.execute(query).fetchall()

        print(total_spends_per_dept_result_set)
        total_spends_per_dept = []
        
        # convert tuples of dict
        for segment in total_spends_per_dept_result_set:
            total_spends_per_dept.append({segment[0]: segment[1]})
        
        return total_spends_per_dept
    
    def get_total_bookings(self):
        base_query  = (
            self.db.query(func.count(Request.id))
            .filter(Request.status == RequestStatusEnum.APPROVED.value)
            .filter(Request.organization_id == self.organization_id)
        )

        if self.start_dt:
            base_query = base_query.filter(Request.date_created >= self.start_dt)
        
        if self.end_dt:
            base_query = base_query.filter(Request.date_created <= self.end_dt)
        
        total_bookings: int = base_query.scalar()

        return total_bookings
    
    def get_top_travellers(self):
        self.db.execute(text("SET sql_mode = (SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''))"))
        
        base_query = (
            self.db.query(
                User,
                Group.name.label('department'),
                func.sum(func.datediff(Request.end, Request.start) * Request.rate).label("total_spend"),
                func.count(Request.id).label('travel_count')
            )
            .join(Request, User.id == Request.requester_id)
            .join(GroupMember, GroupMember.member_id == User.id)
            .join(Group, Group.id == GroupMember.group_id)
            .filter(
                Request.organization_id == self.organization_id, 
                Request.status == RequestStatusEnum.APPROVED.value,
                Group.is_deleted == False
            )
        )
        
        if self.start_dt:
            base_query = base_query.filter(Request.date_created >= self.start_dt)

        if self.end_dt:
            base_query = base_query.filter(Request.date_created <= self.end_dt)
        
        top_travellers = (
            base_query
            .group_by(User.id)
            .order_by(func.count(Request.id).desc())
            .limit(5)
            .all()
        )

        response = [
            analytics_schemas.TopTravellersResponse(
                id=user.id,
                name=f"{user.first_name} {user.last_name}",
                travel_count=travel_count,
                department=department,
                total_spend=total_spend,
            )
            for user, department, total_spend, travel_count in top_travellers
        ]

        return response
    
    def get_top_hotels(self):
        self.db.execute(text("SET sql_mode = (SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''))"))

        query = (
            self.db.query(
                Request, 
                func.count(Request.id).label("travel_count"),
               func.sum(func.datediff(Request.end, Request.start) * Request.rate).label("total_spend")
            )
            .filter(
                Request.organization_id == self.organization_id, 
                Request.status == RequestStatusEnum.APPROVED.value
            )
        )

        if self.start_dt:
            query = query.filter(Request.date_created >= self.start_dt)

        if self.end_dt:
            query = query.filter(Request.date_created <= self.end_dt)

        query = (
            query
            .group_by(Request.hotel)
            .order_by(func.count(Request.id).desc())
            .limit(5)
            .all()
        )

        top_hotels =[
             analytics_schemas.TopHotelsResponse(
                id=request.id,
                name=f"{request.hotel}, {request.state}",
                travel_count=travel_count,
                total_spend=total_spend,
            )
            for request, travel_count, total_spend in query
        ]

        return top_hotels
    

    def get_top_destinations(self):
        self.db.execute(text("SET sql_mode = (SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''))"))

        query = (
            self.db.query(
                Request, 
                func.count(Request.id).label("travel_count"),
                func.sum(func.datediff(Request.end, Request.start) * Request.rate).label("total_spend")
            )
            .filter(Request.organization_id == self.organization_id, Request.status == RequestStatusEnum.APPROVED.value)
        )

        if self.start_dt:
            query = query.filter(Request.date_created >= self.start_dt)

        if self.end_dt:
            query = query.filter(Request.date_created <= self.end_dt)

        query = (
            query
            .group_by(Request.city)
            .order_by(func.count(Request.id).desc())
            .limit(5)
            .all()
        )

        top_destinations =[
             analytics_schemas.TopDestinationsResponse(
                id=request.id,
                name=f"{request.city}, {request.state}",
                travel_count=travel_count,
                total_spend=total_spend,
            )
            for request, travel_count, total_spend in query
        ]

        return top_destinations
    
    def get_top_requesters(self):
        query = (
                self.db.query(
                    User,
                    Group.name.label('department'),
                    func.count(Request.id).label('request_count')
                )
                .join(Request, User.id == Request.requester_id)
                .join(GroupMember, GroupMember.member_id == User.id)
                .join(Group, Group.id == GroupMember.group_id)
                .filter(Request.organization_id == self.organization_id, Group.is_deleted == False)
            )
        
        if self.start_dt:
            query = query.filter(Request.date_created >= self.start_dt)

        if self.end_dt:
            query = query.filter(Request.date_created <= self.end_dt)

            
        query = (
            query.group_by(User.id).order_by(func.count(Request.id).desc()).limit(5).all()
        )
        
        top_requesters = [
            analytics_schemas.TopRequestersResponse(
                id=user.id,
                name=f"{user.first_name} {user.last_name}",
                total_requests=request_count,
                department=department
            )
            for user, department, request_count in query
        ]

        return top_requesters
    
    def get_coworkers(self):
        self.db.execute(text("SET sql_mode = (SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''))"))

        base_query = (
            self.db.query(
                User, 
                Group.name.label('department'),
                func.sum(func.datediff(Request.end, Request.start) * Request.rate).label("total_spend"),
                func.count(Request.id).label('travel_count')
            )
            .join(Request, User.id == Request.requester_id)
            .join(GroupMember, GroupMember.member_id == User.id)
            .join(Group, Group.id == GroupMember.group_id)
            .filter(User.is_deleted == False, Group.is_deleted == False)
            .filter(
                Request.organization_id == self.organization_id, 
                Request.status == RequestStatusEnum.APPROVED.value,
                Request.is_deleted == False
            )
        )

        if self.start_dt:
            base_query = base_query.filter(Request.date_created >= self.start_dt)

        if self.end_dt:
            base_query = base_query.filter(Request.date_created <= self.end_dt)
        
        coworkers = (
            base_query
            .group_by(User.id)
            .limit(5)
            .all()
        )

        response = [
            analytics_schemas.CoworkersResponse(
                id=user.id,
                name=f"{user.first_name} {user.last_name}",
                travel_count=travel_count,
                department=department,
                total_spend=total_spend,
            )
            for user, department, total_spend, travel_count in coworkers
        ]

        return response
    
    async def generate_reports(self, body: analytics_schemas.CreateReport, background_task):
        self.db.execute(text("SET sql_mode = (SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''))"))

        response = {}
        total_spend= None
        total_departments= None
        top_requesters= None
        top_travellers= None
        top_hotels= None
        top_destinations= None

        request_query = (
            self.db.query(Request).filter(Request.organization_id == self.organization_id, Request.is_deleted == False)
            .filter(Request.date_created >= self.start_dt)
            .filter(Request.date_created <= self.end_dt)
        )

        response["total_requests"] = sql_count(request_query) if body.total_requests else None
        response["pending_requests"] = sql_count(request_query.filter(Request.status == RequestStatusEnum.PENDING.value)) if body.pending_requests else None
        response["approved_requests"] = sql_count(request_query.filter(Request.status == RequestStatusEnum.APPROVED.value)) if body.approved_requests else None
        response["cancelled_requests"] = sql_count(request_query.filter(Request.status == RequestStatusEnum.REJECTED.value)) if body.cancelled_requests else None
        response["travel_count"] = sql_count(request_query.filter(Request.status == RequestStatusEnum.APPROVED.value)) if body.travel_count else None

        if body.top_requesters:        
            top_requesters = self.get_top_requesters()

        if body.top_travellers:        
            top_travellers = self.get_top_travellers()

        if body.top_hotels:
            top_hotels = self.get_top_hotels()

        if body.top_destinations:
            top_destinations = self.get_top_destinations()

        if body.total_spend:
            total_spend = self.get_total_spend()

        if body.total_departments:
            total_departments = self.get_department_count_in_organization()

        response["total_spend"] = total_spend
        response["total_departments"] = total_departments
        response["top_requesters"] = top_requesters
        response["top_travellers"] = top_travellers
        response["top_hotels"] = top_hotels
        response["top_destinations"] = top_destinations

        filename = self.generate_pdf(name=f"Report from {self.start_dt} - {self.end_dt}", content=response)

        email_service = EmailService()

        filepath = os.path.join("reports", filename)

        await email_service.send(
            title="Report Generated Successfully",
            template_name="report.html",
            recipients=[body.email],
            template_data=body,
            background_task=background_task,
            attachments=[filepath]
        ) 

        return response
    
    def generate_pdf(self, name: str, content: dict):
        """
            Returns the PDF filename
        """
        os.makedirs("reports", exist_ok=True)

        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", style='B', size=14)
        pdf.cell(200, 10, name, ln=True, align='C')

        pdf.ln(4)
        pdf.set_font('Arial', '', 12)

        for key, value in content.items():
            if not value:
                continue
            key = key.replace('_', ' ').title()
            
            if isinstance(value, list):
                pdf.cell(200, 10, f"{key}:", ln=True)

                for item in value:   
                    text_string = (
                        f"Name: {item.name}"
                    )
                    
                    if item.travel_count is not None:
                        text_string += f",  Travel Count: {item.travel_count}"

                    if item.total_requests is not None:
                        text_string += f",  Total Requests: {item.total_requests}"

                    if item.total_spend is not None:
                        text_string += f",  Total Spend: {item.total_spend:,.2f}"
                    
                    if hasattr(item, 'department'):
                        text_string += f",  Department: {item.department}"

                    
                    pdf.cell(0, 10, text_string, ln=True)  

                pdf.ln(4)       
                 
            else:
                pdf.multi_cell(0, 10, txt=f"{key}: {value}")
                pdf.ln(4)

        # Save the PDF
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename = f"analytics_report_{timestamp}.pdf"
        pdf.output(f"reports/{filename}")
        print("PDF created successfully.")

        return filename