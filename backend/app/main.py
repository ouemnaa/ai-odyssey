"""FastAPI application configuration and entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.routes import analysis, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting Blockchain Forensics API...")
    logger.info("📊 API available at http://localhost:8000")
    logger.info("📖 Documentation at http://localhost:8000/docs")
    yield
    # Shutdown
    logger.info("🛑 Shutting down Blockchain Forensics API...")


# Create FastAPI app
app = FastAPI(
    title="Blockchain Forensics API",
    description="Real-time blockchain forensics and token analysis engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(analysis.router)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint"""
    return {
        "message": "Blockchain Forensics API",
        "docs": "/docs",
        "status": "online"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
