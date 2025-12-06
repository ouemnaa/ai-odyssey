"""Status tracking schemas"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AnalysisStatus(str, Enum):
    """Status states for analysis"""
    QUEUED = "queued"
    FETCHING_DATA = "fetching_data"
    BUILDING_GRAPH = "building_graph"
    DETECTING_PATTERNS = "detecting_patterns"
    COMPLETED = "completed"
    FAILED = "failed"


class StatusResponse(BaseModel):
    """Real-time analysis status"""
    analysisId: str = Field(..., description="Analysis ID")
    status: AnalysisStatus = Field(..., description="Current status")
    progress: int = Field(..., ge=0, le=100, description="Completion percentage")
    currentStep: str = Field(default="", description="Description of current step")
    startedAt: datetime = Field(..., description="When analysis started")
    completedAt: Optional[datetime] = Field(None, description="When analysis completed")
    errorMessage: Optional[str] = Field(None, description="Error details if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "analysisId": "550e8400-e29b-41d4-a716-446655440000",
                "status": "detecting_patterns",
                "progress": 75,
                "currentStep": "Detecting wash trading patterns...",
                "startedAt": "2025-12-06T10:30:00Z"
            }
        }
