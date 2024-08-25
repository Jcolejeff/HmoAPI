from api.v1.logs import schemas as log_schemas
from api.core.base.services import Service
import string
from fastapi import BackgroundTasks


# class LogService(Service):
#     def __init__(self) -> None:
#         super().__init__()

#     @classmethod
#     async def create(cls, payload: log_schemas.LogBase):
#         """
#             Creates an activity log. 
#             Returns `None` if Mongo is not initialized.
#         """
#         activity_message = f'{string.capwords(payload["name"])} {payload["action"]} {payload["message"]}'
#         payload["activity_message"] = activity_message

#         if db is None:
#             print('MongoDB is not setup. Skipping activity log...')
#             return

#         return db.activity_logs.insert_one(payload)

#     @classmethod
#     async def fetch_all(cls, id: int, entity: str):
#         """
#             Gets activity logs for an entity. 
#             Returns `None` if Mongo is not initialized.
#         """
#         if db is None:
#             print('MongoDB is not setup. Skipping activity log...')
#             return

#         logs = db.activity_logs.find({"entity_id": id, "entity": entity}, {
#                                      "_id": 0, "activity_message": 1})

#         return list(logs)
