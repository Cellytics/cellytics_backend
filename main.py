# main.py - Clean, thin application entry point
# All business logic moved to routers/ and services/

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import logging
from datetime import datetime

from database import close_db

# Import routers
from routers import auth, admin, reports, dashboards, notifications, uploads

# ═══════════════════════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BLW Cell Reporting System",
    description="Mobile-first cell report & dashboard system",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:3000",
    "https://cellytics-backend.vercel.app/",],
allow_origin_regex=r"https://.*\.vercel\.app",
    # allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# SWAGGER
# ═══════════════════════════════════════════════════════════════════════════════

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi


# ═══════════════════════════════════════════════════════════════════════════════
# LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    logger.info("🚀 BLW Cell Track API starting...")

@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 Shutting down...")
    await close_db()


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "BLW Cell Reporting API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# INCLUDE ROUTERS
# ═══════════════════════════════════════════════════════════════════════════════

app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(dashboards.router, prefix="/api", tags=["Dashboards"])
app.include_router(notifications.router, prefix="/api", tags=["Notifications"])
app.include_router(uploads.router, prefix="/api", tags=["Uploads"])

# ═══════════════════════════════════════════════════════════════════════════════
# That's it! Everything else is in routers/ and services/
# ═══════════════════════════════════════════════════════════════════════════════













