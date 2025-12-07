"""Mixer detection API routes with AI report and graph data"""

import asyncio
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.services.mixer_service import get_mixer_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mixer", tags=["mixer"])


@router.post("/analyze/{token_address}")
async def analyze_token_for_mixers(
    token_address: str,
    max_hops: int = 3
) -> Dict[str, Any]:
    """
    Analyze a token for mixer connections with AI-generated report.
    
    Returns:
    - textReport: Human-readable AI analysis (markdown format)
    - graphData: JSON structure for visualization (nodes, edges, stats)
    - summary: Key metrics
    
    Args:
        token_address: ERC-20 token contract address
        max_hops: Maximum hops for provenance tracing (default: 3)
    """
    if not token_address.startswith("0x") or len(token_address) != 42:
        raise HTTPException(
            status_code=400,
            detail="Invalid token address format (must be 0x followed by 40 hex characters)"
        )
    
    try:
        logger.info(f"🔍 Mixer analysis requested for token: {token_address}")
        
        mixer_service = get_mixer_service()
        
        if mixer_service.agent is None:
            logger.info("Initializing mixer detection agent...")
            await asyncio.to_thread(mixer_service.initialize_agent)
        
        # Run analysis
        result = await mixer_service.analyze_token_for_mixers(
            token_address=token_address,
            max_hops=max_hops
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Mixer analysis failed: {result.get('error', 'Unknown error')}"
            )
        
        # Format response for frontend
        report = result.get("report", {})
        
        return {
            "status": "success",
            "analysisId": token_address,
            "result": {
                # AI-generated text report (for description under graph)
                "textReport": _generate_text_report(report),
                
                # Structured JSON for graph visualization
                "graphData": _extract_graph_data(report),
                
                # Summary metrics
                "summary": {
                    "tokenAddress": token_address,
                    "analysisTime": result.get("analysis_duration", "N/A"),
                    "timestamp": result.get("timestamp"),
                    "mixersDetected": len(report.get("mixer_detection_results", {}).get("detailed_mixer_reports", [])),
                    "walletsExposed": report.get("wallet_exposure_analysis", {}).get("summary", {}).get("wallets_with_mixer_exposure", 0),
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Error in mixer analysis endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Mixer analysis failed: {str(e)}"
        )


def _generate_text_report(report: Dict[str, Any]) -> str:
    """
    Generate human-readable AI report from mixer analysis.
    This is displayed as description under the graph.
    
    Prefers the original text report from first-flow agent if available.
    """
    try:
        # Use original text report from first-flow agent if available
        if report.get("original_text_report"):
            return report.get("original_text_report")
        
        # Fallback: generate from structured data
        exec_summary = report.get("execution_summary", {})
        mixer_results = report.get("mixer_detection_results", {})
        wallet_analysis = report.get("wallet_exposure_analysis", {})
        network_analysis = report.get("network_analysis", {})
        
        text_parts = [
            "**Mixer Detection Report**",
            f"**Token Address Analyzed:** {exec_summary.get('token_address', 'N/A')}",
            "",
            "---",
            "",
            "### *Summary*",
            f"- *Analysis Time:* {exec_summary.get('analysis_duration_seconds', 0)} seconds",
            f"- *Transactions Analyzed:* {exec_summary.get('data_processed', {}).get('transactions_analyzed', 0)}",
            f"- *Unique Wallets:* {exec_summary.get('data_processed', {}).get('unique_wallets', 0)}",
            f"- *Mixers Detected:* {mixer_results.get('summary', {}).get('total_mixers_detected', 0)}",
            "",
            "---",
        ]
        
        # Mixer Details
        detailed_mixers = mixer_results.get("detailed_mixer_reports", [])
        if detailed_mixers:
            text_parts.append("")
            text_parts.append("### *Mixers Detected*")
            
            for mixer in detailed_mixers[:5]:  # Top 5 mixers
                text_parts.append("")
                text_parts.append(f"**Address:** {mixer.get('address', 'N/A')}")
                text_parts.append(f"**Score:** {mixer.get('score', 0):.3f} ({mixer.get('classification', 'Unknown')})")
                text_parts.append(f"**Type:** {mixer.get('mixer_type', 'Unknown')}")
                
                heuristics = mixer.get('heuristic_scores', {})
                if heuristics:
                    text_parts.append("**Reasoning:**")
                    if 'fan_in' in heuristics:
                        fan_in_val = heuristics['fan_in']
                        # Handle both int/float and dict formats
                        if isinstance(fan_in_val, dict):
                            fan_in_val = fan_in_val.get('value', fan_in_val)
                        text_parts.append(f"- *Fan-in:* {fan_in_val} (high inflow of funds)")
                    if 'fan_out' in heuristics:
                        fan_out_val = heuristics['fan_out']
                        if isinstance(fan_out_val, dict):
                            fan_out_val = fan_out_val.get('value', fan_out_val)
                        text_parts.append(f"- *Fan-out:* {fan_out_val} (high outflow of funds)")
                    if 'temporal_randomness' in heuristics:
                        temporal = heuristics['temporal_randomness']
                        if isinstance(temporal, dict):
                            temporal = temporal.get('score', 0)
                        text_parts.append(f"- *Temporal Score:* {temporal:.2f}" if isinstance(temporal, (int, float)) else f"- *Temporal Score:* {temporal}")
                    if 'uniform_denominations' in heuristics or 'uniform_score' in heuristics:
                        uniform_key = 'uniform_score' if 'uniform_score' in heuristics else 'uniform_denominations'
                        uniform_val = heuristics[uniform_key]
                        if isinstance(uniform_val, dict):
                            uniform_val = uniform_val.get('score', uniform_val)
                        text_parts.append(f"- *Uniform Denominations:* {uniform_val} (fixed amount usage pattern)")
        
        # Wallet Exposure
        wallet_summary = wallet_analysis.get("summary", {})
        if wallet_summary.get("wallets_with_mixer_exposure", 0) > 0:
            text_parts.append("")
            text_parts.append("---")
            text_parts.append("")
            text_parts.append("### *Exposed Wallets*")
            text_parts.append(f"{wallet_summary.get('wallets_with_mixer_exposure', 0)} wallets interacted with mixers")
            
            high_risk = wallet_analysis.get("high_risk_wallets", [])[:5]
            if high_risk:
                text_parts.append("")
                for i, wallet in enumerate(high_risk, 1):
                    addr = wallet.get('address', 'N/A')
                    risk = wallet.get('risk_assessment', {}).get('risk_level', 'UNKNOWN')
                    text_parts.append(f"{i}. {addr[:20]}... ({risk})")
        
        # Network Statistics
        if network_analysis:
            text_parts.append("")
            text_parts.append("---")
            text_parts.append("")
            text_parts.append("### *Network Statistics*")
            
            stats = network_analysis.get("graph_statistics", {})
            if stats.get("avg_degree"):
                text_parts.append(f"- *Average Degree:* {stats.get('avg_degree', 0):.2f} (transactions per wallet)")
            if stats.get("connected_components"):
                text_parts.append(f"- *Connected Components:* {stats.get('connected_components', 0)} (indicating network fragmentation)")
        
        # Key Observations
        insights = report.get("actionable_insights", {})
        if insights.get("immediate_actions"):
            text_parts.append("")
            text_parts.append("---")
            text_parts.append("")
            text_parts.append("### *Key Observations*")
            for action in insights.get("immediate_actions", [])[:3]:
                text_parts.append(f"1. {action}")
        
        # Recommendation
        if insights.get("recommendations"):
            text_parts.append("")
            text_parts.append(f"**Recommendation:** {insights.get('recommendations', ['No specific recommendation'])[0]}")
        
        return "\n".join(text_parts)
        
    except Exception as e:
        logger.error(f"Error generating text report: {e}")
        return f"Error generating report: {str(e)}"


def _extract_graph_data(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract graph visualization data from mixer analysis.
    Returns nodes and edges for rendering in frontend.
    """
    try:
        visualization = report.get("visualization_data", {})
        mixer_results = report.get("mixer_detection_results", {})
        wallet_analysis = report.get("wallet_exposure_analysis", {})
        network_analysis = report.get("network_analysis", {})
        
        # Get nodes from visualization
        nodes = visualization.get("nodes", [])
        
        # Get mixer addresses for coloring
        mixer_addresses = set(m.get("address") for m in mixer_results.get("detailed_mixer_reports", []))
        
        # Enhance nodes with mixer info
        enhanced_nodes = []
        for node in nodes:
            node_id = node.get("id")
            is_mixer = node_id in mixer_addresses
            risk_score = node.get("risk_score", 0)
            
            enhanced_node = {
                "id": node_id,
                "label": node_id[:10] + "..." if node_id else "Unknown",
                "type": "mixer" if is_mixer else "wallet",
                "risk_score": risk_score,
                "size": node.get("size", 5),
                "mixer_type": node.get("mixer_type", ""),
                "color": _get_node_color("mixer" if is_mixer else "wallet", risk_score)
            }
            enhanced_nodes.append(enhanced_node)
        
        # Get edges from visualization
        edges = visualization.get("edges", [])
        
        # Transform edges for graph rendering
        enhanced_edges = []
        for edge in edges:
            source_id = edge.get("source")
            is_mixer_connection = source_id in mixer_addresses
            
            enhanced_edge = {
                "source": source_id,
                "target": edge.get("target"),
                "value": edge.get("value", 0),
                "transactions": edge.get("transactions", 1),
                "type": "mixer_connection" if is_mixer_connection else "transfer",
                "color": "#ff0055" if is_mixer_connection else "#00ff41"
            }
            enhanced_edges.append(enhanced_edge)
        
        return {
            "nodes": enhanced_nodes,
            "edges": enhanced_edges,
            "statistics": {
                "totalNodes": len(nodes),
                "totalEdges": len(edges),
                "mixersDetected": mixer_results.get("summary", {}).get("total_mixers_detected", 0),
                "walletsExposed": wallet_analysis.get("summary", {}).get("wallets_with_mixer_exposure", 0),
                "networkStats": network_analysis.get("graph_statistics", {})
            }
        }
        
    except Exception as e:
        logger.error(f"Error extracting graph data: {e}")
        return {
            "nodes": [],
            "edges": [],
            "statistics": {}
        }


def _get_node_color(node_type: str, risk_score: float) -> str:
    """Determine node color based on type and risk score"""
    if node_type == "mixer":
        if risk_score > 0.8:
            return "#ff0055"  # Red - Critical mixer
        elif risk_score > 0.7:
            return "#ffaa00"  # Orange - High risk mixer
        else:
            return "#ff6600"  # Dark orange - Medium risk mixer
    else:
        # Wallet node
        if risk_score > 0.8:
            return "#ff0055"  # Red - High exposure
        elif risk_score > 0.5:
            return "#ffaa00"  # Orange - Medium exposure
        else:
            return "#00ff41"  # Green - Low exposure


@router.get("/health")
async def mixer_health_check() -> dict:
    """Check mixer service health"""
    try:
        mixer_service = get_mixer_service()
        agent_ready = await asyncio.to_thread(mixer_service.initialize_agent)
        
        return {
            "status": "healthy" if agent_ready else "degraded",
            "mixer_service": "active",
            "agent_ready": agent_ready,
            "agent_url": "http://127.0.0.1:5001",
            "instructions": "Start agent with: python agent/first-flow/mixer_mcp_tool.py"
        }
    except Exception as e:
        logger.error(f"Mixer health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "instructions": "Start agent with: python agent/first-flow/mixer_mcp_tool.py"
        }
