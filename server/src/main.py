"""
Main FastAPI application entry point.
This file imports and mounts FastAPI applications from subfolders.
"""
from chatagent import initialize_chatagent, chatagent_router
from openai_v1 import v1_router
from usage import router as usage_router
from apikey import router as apikey_router
from user import router as user_router
from database import init_database, create_default_admin_user, close_database
from logger import initialize_logger, shutdown_logging
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import sys
from pathlib import Path

# Add the workspace root to Python path so we can import src modules
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))


# Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    """
    # Initialize database first (required for logger database handler)
    init_database()

    # Initialize logger system (must be after database initialization)
    initialize_logger()

    # Create default admin user if configured
    create_default_admin_user()

    # Initialize chatbot module
    await initialize_chatagent()

    # The application runs here
    yield

    # Shutdown logic
    shutdown_logging()
    close_database()

# Create the main FastAPI application
app = FastAPI(
    title="My OpenAI Frontend API",
    description="A FastAPI application that proxies requests to Triton Inference Server with OAuth2 authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for container orchestration and monitoring.

    Returns:
        dict: Health status information including:
            - status: "healthy" if the service is operational
            - version: API version
            - service: Service name
            - database: Database connection status
    """
    from database import get_engine
    from sqlalchemy import text

    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "service": "My OpenAI Frontend API",
        "database": "unknown"
    }

    # Check database connectivity
    try:
        engine = get_engine()
        if engine:
            # Try to execute a simple query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            health_status["database"] = "connected"
        else:
            health_status["database"] = "not initialized"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database"] = f"error: {str(e)}"

    return health_status


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint providing API information.

    Returns:
        dict: Basic API information and links
    """
    return {
        "message": "My OpenAI Frontend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================================
# Include Module Routers
# ============================================================================

# Import routers from modules

# Include routers
app.include_router(user_router, prefix="", tags=[
                   "Authentication", "User Management"])
app.include_router(apikey_router, prefix="", tags=["API Keys"])
app.include_router(usage_router, prefix="", tags=["Usage", "Admin Health"])
app.include_router(v1_router, prefix="", tags=["OpenAI API v1"])
app.include_router(chatagent_router, prefix="", tags=["Chatbot"])

# ============================================================================
# Middleware Configuration
# ============================================================================

# Configure CORS middleware - must be added AFTER AuthMiddleware to process CORS first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow the React app domain
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
