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


# ==================== PageRank Analysis Schemas ====================


class PageRankMetrics(BaseModel):
    """PageRank metrics for a wallet node"""
    walletAddress: str = Field(..., description="Wallet address")
    pageRankScore: float = Field(..., ge=0.0, le=1.0, description="Normalized PageRank score (0-1)")
    inDegree: int = Field(..., ge=0, description="Number of incoming connections")
    outDegree: int = Field(..., ge=0, description="Number of outgoing connections")
    isWhale: bool = Field(default=False, description="Whether wallet is a major token holder")
    tokenBalance: float = Field(default=0.0, description="Token holdings amount")
    influence: str = Field(..., description="Influence level: 'very_high', 'high', 'medium', 'low'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "walletAddress": "0x1234567890123456789012345678901234567890",
                "pageRankScore": 0.0847,
                "inDegree": 47,
                "outDegree": 23,
                "isWhale": True,
                "tokenBalance": 125000.0,
                "influence": "high"
            }
        }


class InfluencerDumpingRisk(BaseModel):
    """Risk assessment for token dumping by influential wallets"""
    walletAddress: str = Field(..., description="Wallet address")
    pageRankScore: float = Field(..., ge=0.0, le=1.0, description="PageRank influence score")
    tokenBalance: float = Field(..., ge=0.0, description="Token holdings amount")
    outgoingVolume: float = Field(..., ge=0.0, description="Recent outgoing transaction volume")
    riskScore: float = Field(..., ge=0, le=100, description="Dumping risk score (0-100)")
    riskLevel: str = Field(..., description="Risk level: 'critical', 'high', 'medium', 'low'")
    lastActivityTime: Optional[datetime] = Field(None, description="Last transaction time")
    dumpingProbability: float = Field(..., ge=0.0, le=1.0, description="Estimated dumping probability (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "walletAddress": "0x1234567890123456789012345678901234567890",
                "pageRankScore": 0.0847,
                "tokenBalance": 125000.0,
                "outgoingVolume": 2500.0,
                "riskScore": 72.5,
                "riskLevel": "high",
                "dumpingProbability": 0.42
            }
        }


class PageRankStats(BaseModel):
    """Statistical summary of PageRank distribution"""
    mean: float = Field(..., description="Mean PageRank score")
    median: float = Field(..., description="Median PageRank score")
    std_dev: float = Field(..., description="Standard deviation")
    max_score: float = Field(..., description="Maximum PageRank score")
    min_score: float = Field(..., description="Minimum PageRank score")
    percentile_95: float = Field(..., description="95th percentile score")
    percentile_99: float = Field(..., description="99th percentile score")

