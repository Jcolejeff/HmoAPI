import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from api.db.database import create_database
# from api.db.mongo import create_nosql_db
from scripts.seed_roles import seed_roles
from api.v1.auth.router import app as auth
from api.v1.user.router import app as users
from api.v1.organization.router import app as organizations
from api.v1.groups.router import app as group
from api.v1.hotels.router import app as hotels
from api.v1.requests.router import app as requests
from api.v1.comments.router import app as comments
from api.v1.closed.router import app as closed
from api.v1.analytics.router import app as analytics
# from api.v1.hotels.router import app as hotels
from api.v1.files.router import app as files

app = FastAPI()

create_database()
# create_nosql_db()


# TODO: Switch to lifespan event handler
@app.on_event("startup")
def startup():
    seed_roles()


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="^http(?:s)?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth, tags=["Auth"], prefix="/v1")
app.include_router(users, tags=["Users"], prefix="/v1")
app.include_router(organizations, tags=["Organizations"], prefix="/v1")
app.include_router(group, tags=["Groups"], prefix="/v1")
app.include_router(hotels, tags=["Hotels"], prefix="/v1")
app.include_router(requests, tags=["Requests"], prefix="/v1")
app.include_router(comments, tags=["Comments"], prefix="/v1")
app.include_router(analytics, tags=["Analytics"], prefix="/v1")
app.include_router(closed, tags=["Closeds"], prefix="/v1")
# app.include_router(hotels, tags=["Hotels"], prefix="/v1")
app.include_router(files, tags=["Files"], prefix="/v1")



@app.get("/", tags=["Home"])
async def get_root(request: Request) -> dict:
    return {
        "message": "Welcome to HMO API",
        "URL": "",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", port=7001, reload=True)
