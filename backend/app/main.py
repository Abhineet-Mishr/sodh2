from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, users, literature, deep_explore

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Parse CORS origins
origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

# Add CORS Middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(literature.router, prefix=f"{settings.API_V1_STR}/literature", tags=["literature"])
app.include_router(deep_explore.router, prefix=f"{settings.API_V1_STR}/deep-explore", tags=["deep_explore"])

@app.get("/")
def root():
    return {"message": "Welcome to SODH API"}

from app.routers import convert, deduplicate, download, review, research_suggestions

app.include_router(convert.router)
app.include_router(deduplicate.router)
app.include_router(download.router)
app.include_router(review.router)
app.include_router(research_suggestions.router)
