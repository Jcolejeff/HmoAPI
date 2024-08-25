# from pymongo import MongoClient
# from api.utils import settings
# from pymongo.mongo_client import MongoClient


# def create_nosql_db():
#     if not settings.MONGO_URI:
#         return

#     client = MongoClient(settings.MONGO_URI)

#     try:
#         client.admin.command("ping")
#         print("MongoDB Connection Established...")
#     except Exception as e:
#         print(e)


# client = MongoClient(settings.MONGO_URI) if settings.MONGO_URI else None
# db = client.get_database(
#     settings.MONGO_DB_NAME) if settings.MONGO_DB_NAME else None
