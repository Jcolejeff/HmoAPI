import openai
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from api.v1.requests import schemas as req_schemas
from api.db.database import get_db
from api.v1.comments.services import CommentService
from api.v1.comments import schemas as comment_schemas
from api.v1.closed.services import ClosedService
from api.v1.closed import schemas as closed_schemas

class OpenAiService:
    def __init__(self, api_key: str, db: Session) -> None:
        self.api_key = api_key
        self.db = db
        openai.api_key = self.api_key
        openai.api_base = "https://openrouter.ai/api/v1"
        
    async def call_openai(self, payload: req_schemas.UpdateRequest, request_id: int, author_id: int):
        # Fetch comments asynchronously
        comments, total = await CommentService.fetch_all(
            db=self.db,
            table_name=comment_schemas.EntityNameEnum.REQUEST,
            organization_id=payload.organization_id,
            record_id=request_id,
            parent_id=None,
            offset=0,
            size=100
        )

        # Process each comment to extract the necessary information
        processed_comments = []
        for comment in comments:
            full_name = f"{comment.creator.first_name} {comment.creator.last_name}"
            role_name = None

            # Find the role name based on the organization_id
            for user_org in comment.creator.user_orgs:
                if user_org.organization_id == payload.organization_id:
                    role_name = user_org.role.name
                    break

            # Create a dictionary with the desired fields
            processed_comment = {
                "content": comment.content,
                "creator_name": full_name,
                "role": role_name
            }

            processed_comments.append(processed_comment)

        print(processed_comments)  # This will print the processed comments

        # Make the OpenAI API call
        try:
            response = openai.ChatCompletion.create(
                model="nousresearch/hermes-3-llama-3.1-405b",
                messages=[
                    {"role": "user", "content": f"return an object with three fields: request_id: {request_id}, org_id:{payload.organization_id}, author_id:{author_id}, status: {payload.status}, department:{payload.hotel}, Comments: {processed_comments}. Return nothing else but the object, no comments or thoughts, just the object, please."},
                ],
            )
            print(response['choices'][0]["message"]["content"])
        except Exception as e:
            print(f"Error during OpenAI API call: {e}")
            return None  # Or handle the error appropriately

        # Convert the dictionary into the Pydantic model
        data = closed_schemas.ClosedCreate(
            organization_id=payload.organization_id,
            content=response['choices'][0]["message"]["content"],
        )

        closed = await ClosedService.create(payload=data, created_by=author_id, db=self.db)
        print(closed_schemas.ShowClosed.model_validate(closed))