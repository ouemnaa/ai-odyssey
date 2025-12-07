"""Schemas for mixer detection and flagging analysis"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class MixerRiskLevel(str, Enum):
    """Risk levels for mixer detection"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MixerClassification(str, Enum):
    """Mixer classification types"""
    HIGH_RISK_MIXER = "HIGH_RISK_MIXER"
    MEDIUM_RISK_MIXER = "MEDIUM_RISK_MIXER"
    LOW_RISK_MIXER = "LOW_RISK_MIXER"


class HeuristicScore(BaseModel):
    """Score for a single heuristic"""
    score: float = Field(..., description="Heuristic score 0-1")
    value: Optional[float | int | str] = Field(None, description="Raw value measured")
    weight: float = Field(..., description="Weight in overall calculation")
    interpretation: str = Field(..., description="Human-readable interpretation")


class FlagDetection(BaseModel):
    """A single detected flag"""
    flag: str = Field(..., description="Flag identifier")
    detected: bool = Field(..., description="Whether flag was detected")
    description: str = Field(..., description="Flag description")


class TransactionStatistics(BaseModel):
    """Transaction statistics for mixer"""
    total_incoming: int = Field(..., description="Number of incoming transactions")
    total_outgoing: int = Field(..., description="Number of outgoing transactions")
    total_transactions: int = Field(..., description="Total transactions")
    total_incoming_amount: float = Field(..., description="Total incoming amount")
    total_outgoing_amount: float = Field(..., description="Total outgoing amount")
    avg_incoming_amount: float = Field(..., description="Average incoming amount")
    avg_outgoing_amount: float = Field(..., description="Average outgoing amount")


class MixerReport(BaseModel):
    """Detailed mixer detection report"""
    address: str = Field(..., description="Mixer address")
    score: float = Field(..., description="Overall mixer score 0-1")
    mixer_type: str = Field(..., description="Type of mixer detected")
    classification: MixerClassification = Field(..., description="Risk classification")
    
    transaction_statistics: TransactionStatistics = Field(..., description="TX stats")
    
    heuristic_scores: Dict[str, Dict[str, Any]] = Field(
        ..., 
        description="Scores for each heuristic (fan_in, fan_out, uniform_denominations, temporal_randomness)"
    )
    
    flags_detected: List[FlagDetection] = Field(..., description="All detected flags")
    
    weighted_calculation: Dict[str, Any] = Field(
        ...,
        description="Explanation of weighted calculation"
    )
    
    top_connections: Dict[str, List[str]] = Field(
        ...,
        description="Top senders and receivers"
    )
    
    summary: str = Field(..., description="Human-readable summary")


class WalletExposureSummary(BaseModel):
    """Summary of wallet exposure to mixers"""
    exposed_to_mixers: bool = Field(..., description="Whether wallet has mixer exposure")
    number_of_mixers: int = Field(..., description="Number of unique mixers connected")
    total_provenance_paths: int = Field(..., description="Total paths to mixers")
    avg_distance_to_mixers: float = Field(..., description="Average hops to mixers")
    max_mixer_score: float = Field(..., description="Highest mixer score detected")
    avg_mixer_score: float = Field(..., description="Average mixer score")
    forward_paths: int = Field(..., description="Paths going forward in time")
    backward_paths: int = Field(..., description="Paths going backward in time")


class RiskAssessment(BaseModel):
    """Risk assessment for wallet"""
    risk_score: float = Field(..., description="Overall risk score 0-1")
    risk_level: MixerRiskLevel = Field(..., description="Risk level classification")
    risk_factors: List[str] = Field(..., description="List of risk factors")


class WalletMixerReport(BaseModel):
    """Mixer exposure report for specific wallet"""
    address: str = Field(..., description="Wallet address")
    exposure_summary: WalletExposureSummary = Field(..., description="Exposure summary")
    risk_assessment: RiskAssessment = Field(..., description="Risk assessment")
    provenance_details: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Details of provenance paths"
    )
    summary: str = Field(..., description="Human-readable summary")


class MixerAnalysisReport(BaseModel):
    """Complete mixer analysis report"""
    token_address: str = Field(..., description="Token analyzed")
    analysis_timestamp: str = Field(..., description="When analysis was performed")
    analysis_duration: str = Field(..., description="How long analysis took")
    
    mixer_detection: Dict[str, Any] = Field(
        ...,
        description="Mixer detection summary"
    )
    
    detailed_mixer_reports: List[MixerReport] = Field(
        ...,
        description="Detailed reports for each detected mixer"
    )
    
    wallet_exposure_reports: List[WalletMixerReport] = Field(
        ...,
        description="Wallet exposure reports"
    )
    
    network_analysis: Dict[str, Any] = Field(
        ...,
        description="High-level network analysis"
    )
    
    summary: str = Field(..., description="Executive summary of findings")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token_address": "0x...",
                "analysis_timestamp": "2025-12-07T10:30:00",
                "analysis_duration": "12.34s",
                "mixer_detection": {
                    "mixers_detected": 3,
                    "total_mixer_score": 2.4,
                    "critical_mixers": 1,
                    "high_risk_mixers": 1,
                    "medium_risk_mixers": 1
                },
                "detailed_mixer_reports": [],
                "wallet_exposure_reports": [],
                "network_analysis": {},
                "summary": "Analysis found 3 potential mixers with critical risk exposure"
            }
        }
