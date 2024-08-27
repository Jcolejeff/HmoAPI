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
        issue_object = {
                "description": payload.purpose,
                "department": payload.state,
                "start_date": payload.start,
                "faculty": payload.hotel,
                "level": payload.rate
        }
        print(issue_object)
        #Make the OpenAI API call
        try:
            response = openai.ChatCompletion.create(
                model="nousresearch/hermes-3-llama-3.1-405b",
                messages=[
                    {"role": "user", "content": f"So i have a pretty interesting task for you , i would give you an issue object that has fields like department,level(school year in uni), decription of issue, and the comments on that issue, my frontend is a ticket management software for a university, so i want it so that when a ticket is approved or closed, i generate a summary of that issue , and have a page where other students can see the resolved issues, incase they have a similar issue, so i want you to look at the issue object, get the title from the description , get the issue, and get the solution , it's very importat to go through the comments so you can have more insights as the how the issue was resolved, the latest convo is the last item in the comments array , so what i want you to return is an object with these fields ,  title:, issue:, and solution: ,  these are the comments  - Comments: {processed_comments} and this is the issue object:{issue_object} . Return nothing else but the object, no comments or thoughts, just the object, please.just the object with the fields i mentioned, thanks, which are title,issue, solution" },
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