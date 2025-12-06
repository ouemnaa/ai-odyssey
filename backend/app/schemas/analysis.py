"""Request and response schemas for analysis endpoints"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TokenAddressRequest(BaseModel):
    """Request to analyze a token"""
    tokenAddress: str = Field(..., min_length=42, max_length=42, description="ERC-20 contract address (0x...)")
    daysBack: int = Field(default=7, ge=1, le=90, description="Days of history to analyze")
    sampleSize: Optional[int] = Field(default=1000, ge=100, le=10000, description="Max transactions to fetch")

    class Config:
        json_schema_extra = {
            "example": {
                "tokenAddress": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
                "daysBack": 7,
                "sampleSize": 5000
            }
        }


class AnalysisRequest(BaseModel):
    """Unified analysis request"""
    type: str = Field(default="token", description="Type: 'token' or 'wallet'")
    address: str = Field(..., min_length=42, description="Address to analyze")
    parameters: Optional[TokenAddressRequest] = None


class AnalysisResponse(BaseModel):
    """Response when submitting analysis"""
    analysisId: str = Field(..., description="Unique analysis ID for tracking")
    status: str = Field(default="processing", description="Current status: processing, completed, failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When analysis was submitted")
    estimatedCompletionTime: Optional[datetime] = Field(None, description="Estimated completion time")

    class Config:
        json_schema_extra = {
            "example": {
                "analysisId": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "timestamp": "2025-12-06T10:30:00Z"
            }
        }


class ExportRequest(BaseModel):
    """Export format request"""
    format: str = Field(default="json", description="Export format: 'csv' or 'json'")
    includeMetadata: bool = Field(default=True, description="Include metadata in export")
