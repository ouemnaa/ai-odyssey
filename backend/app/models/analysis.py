"""SQLAlchemy database models"""

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Analysis(Base):
    """Database model for storing analysis results and metadata"""
    __tablename__ = "analyses"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Input
    tokenAddress = Column(String(42), index=True, nullable=False)
    daysBack = Column(Integer, default=7)
    sampleSize = Column(Integer, default=1000)

    # Status
    status = Column(String(50), default="queued", index=True)  # queued, processing, completed, failed

    # Timing
    createdAt = Column(DateTime, default=datetime.utcnow, index=True)
    startedAt = Column(DateTime, nullable=True)
    completedAt = Column(DateTime, nullable=True)

    # Results
    riskScore = Column(Float, nullable=True)
    nodeCount = Column(Integer, nullable=True)
    edgeCount = Column(Integer, nullable=True)

    # Large data
    resultData = Column(JSON, nullable=True)  # Serialized AnalysisDataModel
    parametersData = Column(JSON, nullable=True)  # Request parameters

    # Metadata
    ipAddress = Column(String(45), nullable=True)
    errorMessage = Column(String(500), nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_token_address_created', 'tokenAddress', 'createdAt'),
        Index('idx_status_created', 'status', 'createdAt'),
    )

    def __repr__(self):
        return f"<Analysis {self.id} for {self.tokenAddress} - {self.status}>"
