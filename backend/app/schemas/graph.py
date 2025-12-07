"""Graph and analysis data models matching frontend AnalysisData interface"""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NodeType(str, Enum):
    """Classification of wallet/node types"""
    SUSPICIOUS = "suspicious"
    NORMAL = "normal"
    DEPLOYER = "deployer"
    MIXER = "mixer"


class NodeModel(BaseModel):
    """Represents a wallet/address node in the graph"""
    id: str = Field(..., description="Wallet or contract address")
    label: str = Field(..., description="Display label for the node")
    group: NodeType = Field(..., description="Classification of node type")
    value: float = Field(..., description="Holdings in tokens or transaction value")
    transactions: int = Field(default=0, description="Number of transactions")
    riskScore: Optional[float] = Field(None, ge=0, le=100, description="Risk score 0-100")
    description: Optional[str] = Field(None, description="Additional information")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "0x1234567890123456789012345678901234567890",
                "label": "Suspicious Wallet",
                "group": "suspicious",
                "value": 1000000.0,
                "transactions": 45,
                "riskScore": 85.5,
                "description": "Involved in wash trading"
            }
        }


class LinkModel(BaseModel):
    """Represents a transaction/connection between wallets"""
    source: str = Field(..., description="Source wallet address")
    target: str = Field(..., description="Target wallet address")
    value: float = Field(..., description="Transaction volume or amount")
    type: str = Field(default="transfer", description="Type: transfer, trade, wash, mixer")
    count: int = Field(default=1, description="Number of transactions in this link")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "0xaaaa...",
                "target": "0xbbbb...",
                "value": 500000.0,
                "type": "wash",
                "count": 12
            }
        }


class RiskMetricsModel(BaseModel):
    """Overall risk metrics for the analyzed token"""
    giniCoefficient: float = Field(..., ge=0, le=1, description="Wealth distribution inequality (0=equal, 1=concentrated)")
    washTradingScore: float = Field(..., ge=0, le=100, description="Wash trading likelihood percentage")
    mixerConnectionsCount: int = Field(..., ge=0, description="Number of suspected mixer connections")
    suspiciousClustersDetected: int = Field(..., ge=0, description="Number of suspicious wallet clusters")


class TopInfluentialWallet(BaseModel):
    """Wallet with significant influence in the network"""
    address: str = Field(..., description="Wallet address")
    pageRankScore: float = Field(..., description="Network centrality score")
    holdings: float = Field(..., description="Token holdings")
    riskLevel: RiskLevel = Field(..., description="Assessed risk level")


class DetectedCommunity(BaseModel):
    """Detected community or cluster of wallets"""
    id: str = Field(..., description="Unique community identifier")
    name: str = Field(..., description="Community name")
    walletCount: int = Field(..., description="Number of wallets in community")
    suspicionLevel: RiskLevel = Field(..., description="Suspicion level of community")
    description: str = Field(..., description="Community description and findings")


class RedFlag(BaseModel):
    """Suspicious pattern or alert"""
    id: str = Field(..., description="Unique flag identifier")
    severity: RiskLevel = Field(..., description="Severity of the flag")
    title: str = Field(..., description="Short title of the issue")
    description: str = Field(..., description="Detailed description")
    affectedWallets: List[str] = Field(default_factory=list, description="Wallet addresses involved")




class AnalysisDataModel(BaseModel):
    """Complete blockchain forensics analysis result"""
    nodes: List[NodeModel] = Field(..., description="List of wallets/addresses")
    links: List[LinkModel] = Field(..., description="List of transactions/connections")
    riskScore: float = Field(..., ge=0, le=100, description="Overall risk score")
    metrics: RiskMetricsModel = Field(..., description="Calculated risk metrics")
    topInfluentialWallets: List[TopInfluentialWallet] = Field(..., description="Most important wallets by centrality")
    detectedCommunities: List[DetectedCommunity] = Field(..., description="Detected communities")
    redFlags: List[RedFlag] = Field(..., description="Suspicious patterns and alerts")
    
    # NEW: PageRank analysis fields
    pageRankMetrics: List["PageRankMetrics"] = Field(default_factory=list, description="PageRank metrics for all analyzed wallets")
    topInfluencers: List["PageRankMetrics"] = Field(default_factory=list, description="Top 20 influential wallets by PageRank score")
    influencerDumpingRisks: List["InfluencerDumpingRisk"] = Field(default_factory=list, description="Dumping risk assessment for influencers")
    pageRankStats: Optional["PageRankStats"] = Field(None, description="Statistical summary of PageRank distribution")

    class Config:
        json_schema_extra = {
            "description": "Complete blockchain forensics analysis result matching frontend AnalysisData interface"
        }


# Import schemas to avoid circular imports
from app.schemas.analysis import PageRankMetrics, InfluencerDumpingRisk, PageRankStats

