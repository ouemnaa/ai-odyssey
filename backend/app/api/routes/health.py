"""Health check endpoints"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "blockchain-forensics-api",
        "version": "1.0.0"
    }


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Blockchain Forensics API",
        "docs": "/docs",
        "status": "online"
    }
