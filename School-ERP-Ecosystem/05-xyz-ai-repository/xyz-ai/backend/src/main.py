import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
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
    # Initialize schema & ensure seed data is present gracefully
    try:
        init_db()
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            if user_count == 0:
                print("[INFO] Database empty. Running initial seed data...")
                seed_database()
        except Exception as e:
            print(f"[WARNING] Database check during startup: {e}")
        finally:
            db.close()
    except Exception as e:
        print(f"[WARNING] Lifespan initialization error: {e}")
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
        "supported_languages_count": 11,
        "nlu_mode": settings.nlu_mode
    }

@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.png", include_in_schema=False)
def favicon():
    return Response(status_code=204)

# Locate Frontend Static Directory (works in local dev and Vercel serverless)
possible_frontend_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend")),
    os.path.abspath(os.path.join(os.getcwd(), "School-ERP-Ecosystem", "05-xyz-ai-repository", "xyz-ai", "frontend")),
    os.path.abspath(os.path.join(os.getcwd(), "frontend")),
]

frontend_dir = None
for p in possible_frontend_paths:
    if os.path.exists(p) and os.path.exists(os.path.join(p, "index.html")):
        frontend_dir = p
        break

if frontend_dir:
    src_dir = os.path.join(frontend_dir, "src")
    if os.path.exists(src_dir):
        app.mount("/src", StaticFiles(directory=src_dir), name="frontend-src")
    
    @app.get("/")
    def serve_frontend_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
