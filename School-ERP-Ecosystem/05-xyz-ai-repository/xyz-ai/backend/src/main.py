import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from src.config import settings
from src.database import init_db, SessionLocal
from src.models import User
from seed.seed_data import seed_database
from src.api.router_auth import router as auth_router
from src.api.router_chat import router as chat_router
from src.api.router_voice import router as voice_router
from src.api.router_escalations import router as escalations_router
from src.api.router_audit import router as audit_router
from src.api.router_portal import router as portal_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize schema & ensure seed data is present
    init_db()
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print("[INFO] Database empty. Running initial seed data...")
            seed_database()
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="XYZ AI — Human-Like School Assistant API with Hardened RBAC, Multi-turn Memory, and Multilingual Voice/Avatar support.",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(voice_router, prefix=settings.API_V1_STR)
app.include_router(escalations_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(portal_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "security_mode": "hardened_rbac_active",
        "rate_limiting": "enabled",
        "supported_languages_count": 11
    }

# Mount Frontend Static Assets
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/src", StaticFiles(directory=os.path.join(frontend_dir, "src")), name="frontend-src")
    
    @app.get("/")
    def serve_frontend_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
