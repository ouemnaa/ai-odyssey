"""Core analysis service - integrates ForensicGraphAgent with database"""

import asyncio
import sys
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for managing token analysis with ForensicGraphAgent"""

    def __init__(self, bitquery_api_key: str = ""):
        """
        Initialize analysis service.

        Args:
            bitquery_api_key: BitQuery API key for fetching blockchain data
        """
        self.bitquery_api_key = bitquery_api_key
        self.agent = None
        self.analyses = {}  # In-memory store for demo (replace with DB)

    async def submit_analysis(self, token_address: str, days_back: int = 7,
                             sample_size: int = 1000) -> str:
        """
        Submit a token for analysis. Returns analysis_id.

        Args:
            token_address: ERC-20 contract address
            days_back: Days of transaction history to analyze
            sample_size: Maximum transactions to fetch

        Returns:
            analysis_id for tracking
        """
        from uuid import uuid4
        analysis_id = str(uuid4())

        # Store analysis metadata
        self.analyses[analysis_id] = {
            "id": analysis_id,
            "tokenAddress": token_address,
            "daysBack": days_back,
            "sampleSize": sample_size,
            "status": "queued",
            "createdAt": datetime.utcnow(),
            "startedAt": None,
            "completedAt": None,
            "progress": 0,
            "currentStep": "Queued for processing",
            "resultData": None,
            "errorMessage": None
        }

        logger.info(f"Analysis submitted: {analysis_id} for token {token_address}")
        return analysis_id

    async def run_analysis(self, analysis_id: str) -> Dict[str, Any]:
        """
        Execute forensic analysis (called by background task).

        Args:
            analysis_id: ID of analysis to run

        Returns:
            Analysis result data
        """
        if analysis_id not in self.analyses:
            raise ValueError(f"Analysis {analysis_id} not found")

        analysis = self.analyses[analysis_id]

        try:
            analysis['status'] = 'fetching_data'
            analysis['startedAt'] = datetime.utcnow()
            analysis['progress'] = 10
            analysis['currentStep'] = 'Initializing ForensicGraphAgent...'

            # Step 1: Initialize agent (run in thread to avoid blocking)
            self.agent = await asyncio.to_thread(
                self._initialize_agent
            )

            analysis['progress'] = 20
            analysis['currentStep'] = 'Fetching transactions from BitQuery...'

            # Step 2: Fetch transactions
            transactions = await asyncio.to_thread(
                self.agent.fetch_real_transactions,
                days_back=analysis['daysBack'],
                limit=analysis['sampleSize'],
                token_contract_address=analysis['tokenAddress']
            )

            if not transactions:
                raise ValueError("No transactions found for this token")

            analysis['progress'] = 40
            analysis['currentStep'] = 'Fetching internal transactions...'

            # Step 3: Fetch internal transactions
            internal_transactions = await asyncio.to_thread(
                self.agent.fetch_real_internal_transactions,
                limit=analysis['sampleSize'] // 5,
                token_contract_address=analysis['tokenAddress']
            )

            analysis['progress'] = 50
            analysis['currentStep'] = 'Building transaction graph...'
            analysis['status'] = 'building_graph'

            # Step 4: Build graph
            await asyncio.to_thread(
                self.agent.build_graph_from_real_data,
                transactions,
                internal_transactions
            )

            analysis['progress'] = 70
            analysis['currentStep'] = 'Fetching token holders...'

            # Step 5: Fetch token holders
            token_holders = await asyncio.to_thread(
                self.agent.fetch_real_token_holders,
                token_address=analysis['tokenAddress'],
                limit=100
            )
            self.agent.token_holders = token_holders

            analysis['progress'] = 75
            analysis['currentStep'] = 'Detecting suspicious patterns...'
            analysis['status'] = 'detecting_patterns'

            # Step 6: Detect patterns
            clusters = await asyncio.to_thread(
                self.agent.detect_all_clusters_real
            )

            analysis['progress'] = 85
            analysis['currentStep'] = 'Calculating risk metrics...'

            # Step 7: Calculate metrics
            clusters = await asyncio.to_thread(
                self.agent.calculate_advanced_risk_metrics,
                clusters
            )

            analysis['progress'] = 90
            analysis['currentStep'] = 'Converting results to frontend format...'

            # Step 8: Convert to frontend format
            from app.utils.graph_converter import convert_forensic_output_to_analysis_data
            analysis_data = await asyncio.to_thread(
                convert_forensic_output_to_analysis_data,
                graph=self.agent.combined_G,
                clusters=clusters,
                agent=self.agent
            )

            # Store results
            analysis['status'] = 'completed'
            analysis['completedAt'] = datetime.utcnow()
            analysis['progress'] = 100
            analysis['currentStep'] = 'Analysis complete'
            analysis['riskScore'] = analysis_data.riskScore
            analysis['nodeCount'] = len(analysis_data.nodes)
            analysis['edgeCount'] = len(analysis_data.links)
            analysis['resultData'] = analysis_data.model_dump()

            logger.info(f"Analysis {analysis_id} completed successfully")
            return analysis_data.model_dump()

        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed: {str(e)}", exc_info=True)
            analysis['status'] = 'failed'
            analysis['errorMessage'] = str(e)
            analysis['completedAt'] = datetime.utcnow()
            raise

    async def get_status(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis status and progress"""
        if analysis_id not in self.analyses:
            raise ValueError(f"Analysis {analysis_id} not found")

        analysis = self.analyses[analysis_id]
        return {
            "analysisId": analysis_id,
            "status": analysis["status"],
            "progress": analysis["progress"],
            "currentStep": analysis["currentStep"],
            "startedAt": analysis["startedAt"],
            "completedAt": analysis["completedAt"],
            "errorMessage": analysis.get("errorMessage")
        }

    async def get_results(self, analysis_id: str) -> Dict[str, Any]:
        """Retrieve analysis results"""
        if analysis_id not in self.analyses:
            raise ValueError(f"Analysis {analysis_id} not found")

        analysis = self.analyses[analysis_id]

        if analysis["status"] != "completed":
            raise ValueError(f"Analysis {analysis_id} not yet completed (status: {analysis['status']})")

        if not analysis["resultData"]:
            raise ValueError("Analysis results not available")

        return analysis["resultData"]

    async def list_recent_analyses(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """List recent analyses"""
        analyses_list = sorted(
            self.analyses.values(),
            key=lambda x: x['createdAt'],
            reverse=True
        )[offset:offset + limit]

        return {
            "total": len(self.analyses),
            "analyses": [
                {
                    "id": a["id"],
                    "tokenAddress": a["tokenAddress"],
                    "status": a["status"],
                    "riskScore": a.get("riskScore"),
                    "createdAt": a["createdAt"],
                    "completedAt": a["completedAt"]
                }
                for a in analyses_list
            ]
        }

    def _initialize_agent(self):
        """Initialize ForensicGraphAgent (runs in thread)"""
        try:
            # Add agent path to sys.path
            agent_path = Path(__file__).parent.parent.parent.parent / "agent" / "second-flow"
            if str(agent_path) not in sys.path:
                sys.path.insert(0, str(agent_path))

            # Import and initialize
            from work import ForensicGraphAgent
            agent = ForensicGraphAgent(api_key=self.bitquery_api_key)

            logger.info("ForensicGraphAgent initialized successfully")
            return agent
        except ImportError as e:
            logger.error(f"Failed to import ForensicGraphAgent: {e}")
            raise Exception(f"Failed to initialize agent: {e}")
