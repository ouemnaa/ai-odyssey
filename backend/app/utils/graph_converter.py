"""Graph converter: transforms ForensicGraphAgent output to frontend AnalysisDataModel"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import logging

from app.schemas.graph import (
    NodeModel, LinkModel, RiskMetricsModel, AnalysisDataModel,
    TopInfluentialWallet, DetectedCommunity, RedFlag, NodeType, RiskLevel
)

logger = logging.getLogger(__name__)


def convert_forensic_output_to_analysis_data(
    graph,
    clusters: List[Dict[str, Any]],
    agent
) -> AnalysisDataModel:
    """
    Convert ForensicGraphAgent output to frontend AnalysisDataModel.

    Args:
        graph: NetworkX DiGraph from agent.combined_G
        clusters: List of detected patterns from agent.detect_all_clusters_real()
        agent: ForensicGraphAgent instance for additional metrics

    Returns:
        AnalysisDataModel ready for frontend consumption
    """
    try:
        # Ensure clusters is a list
        if not clusters:
            clusters = []
        
        logger.info(f"Converting forensic data: graph has {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

        # Filter to top 50 holders by amount
        filtered_graph = _filter_top_holders(graph, top_n=50)
        logger.info(f"Filtered to top 50 holders: {filtered_graph.number_of_nodes()} nodes, {filtered_graph.number_of_edges()} edges")

        # Extract nodes from filtered graph
        nodes = _extract_nodes(filtered_graph, clusters)
        logger.info(f"Extracted {len(nodes)} nodes")

        # Extract links from filtered graph
        links = _extract_links(filtered_graph)
        logger.info(f"Extracted {len(links)} links")

        # Calculate risk metrics
        metrics = _calculate_risk_metrics(graph, clusters)
        logger.info(f"Calculated metrics: gini={metrics.giniCoefficient:.2f}")

        # Get top influential wallets (PageRank)
        top_wallets = _get_top_influential_wallets(graph, nodes)
        logger.info(f"Identified {len(top_wallets)} influential wallets")

        # Extract detected communities
        communities = _extract_communities(clusters)
        logger.info(f"Extracted {len(communities)} communities")

        # Generate red flags from patterns
        red_flags = _generate_red_flags(clusters)
        logger.info(f"Generated {len(red_flags)} red flags")

        # Calculate overall risk score
        risk_score = _calculate_risk_score(metrics, red_flags)
        logger.info(f"Overall risk score: {risk_score:.1f}")

        logger.info(f"Successfully converted forensic data: {len(nodes)} nodes, {len(links)} links, risk={risk_score}")

        return AnalysisDataModel(
            nodes=nodes,
            links=links,
            riskScore=risk_score,
            metrics=metrics,
            topInfluentialWallets=top_wallets,
            detectedCommunities=communities,
            redFlags=red_flags
        )
    except Exception as e:
        logger.error(f"Error converting forensic output: {str(e)}", exc_info=True)
        raise


def _filter_top_holders(graph, top_n: int = 50):
    """Filter graph to only include top N holders by total amount held"""
    # Calculate total holdings for each node (sum of incoming amounts)
    holdings = {}
    for node in graph.nodes():
        total_held = 0
        try:
            for pred in graph.predecessors(node):
                if graph.has_edge(pred, node):
                    total_held += graph[pred][node].get('total_amount', 0)
        except:
            pass
        holdings[node] = total_held
    
    # Get top N holders
    top_holders = sorted(holdings.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_holder_set = {node for node, _ in top_holders}
    
    logger.info(f"Top {top_n} holders (by incoming amount): {[node[:10] + '...' for node, _ in top_holders[:5]]}")
    
    # Create subgraph with only edges between top holders
    filtered_edges = []
    for source, target, data in graph.edges(data=True):
        if source in top_holder_set and target in top_holder_set:
            filtered_edges.append((source, target, data))
    
    # Create new graph with top holders
    filtered_graph = graph.__class__()
    
    # Add nodes
    for node in top_holder_set:
        if node in graph.nodes():
            filtered_graph.add_node(node, **graph.nodes[node])
    
    # Add edges
    for source, target, data in filtered_edges:
        filtered_graph.add_edge(source, target, **data)
    
    return filtered_graph


def _extract_nodes(graph, clusters: List[Dict]) -> List[NodeModel]:
    """Extract nodes with proper classification"""
    nodes = []
    node_risk_scores = _calculate_node_risk_scores(graph, clusters)

    for node_id in graph.nodes():
        node_data = graph.nodes[node_id]

        # Classify node type
        node_type = _classify_node(node_id, node_data, clusters)

        # Calculate holdings (sum of all incoming amounts)
        holdings = 0
        try:
            holdings = sum(
                graph[pred][node_id].get('total_amount', 0)
                for pred in graph.predecessors(node_id)
            )
        except (StopIteration, KeyError):
            pass

        # Transaction count
        tx_count = graph.in_degree(node_id) + graph.out_degree(node_id)

        # Generate label - always ensure it's a string
        annotation = node_data.get('annotation')
        if annotation and isinstance(annotation, str) and annotation.strip():
            label = annotation
        else:
            # Fallback to shortened address
            label = node_id[:12] + '...' if len(node_id) > 12 else node_id

        nodes.append(NodeModel(
            id=node_id,
            label=label,
            group=node_type,
            value=holdings,
            transactions=tx_count,
            riskScore=node_risk_scores.get(node_id, 0)
        ))

    return nodes


def _extract_links(graph) -> List[LinkModel]:
    """Extract edges as links"""
    links = []

    for source, target, data in graph.edges(data=True):
        # Determine link type based on data
        link_type = _classify_link_type(data)

        links.append(LinkModel(
            source=source,
            target=target,
            value=data.get('total_amount', data.get('combined_total', 0)),
            type=link_type,
            count=data.get('tx_count', data.get('combined_count', 1))
        ))

    return links


def _classify_node(node_id: str, node_data: Dict, clusters: List[Dict]) -> NodeType:
    """Classify node as suspicious, normal, deployer, or mixer"""

    # Check if mixer
    if any(
        cluster.get('type') == 'mixer_suspected' and cluster.get('node') == node_id
        for cluster in clusters
    ):
        return NodeType.MIXER

    # Check if suspicious (part of wash trading, ponzi, etc.)
    is_suspicious = any(
        node_id in cluster.get('cycle', []) or
        node_id in cluster.get('pair', []) or
        node_id in cluster.get('wallets', []) or
        node_id in cluster.get('funding_sources', [])
        for cluster in clusters
        if cluster.get('type') in ['circular_trading', 'reciprocal_trading', 'ponzi_suspected']
    )

    return NodeType.SUSPICIOUS if is_suspicious else NodeType.NORMAL


def _calculate_node_risk_scores(graph, clusters: List[Dict]) -> Dict[str, float]:
    """Calculate individual node risk scores (0-100)"""
    scores = {}

    # Base score from degree centrality
    try:
        import networkx as nx
        degree_centrality = nx.degree_centrality(graph)
    except Exception as e:
        logger.warning(f"Could not calculate degree centrality: {e}")
        degree_centrality = {}

    for node_id in graph.nodes():
        score = degree_centrality.get(node_id, 0) * 50  # Max 50 from centrality

        # Add points for cluster involvement
        for cluster in clusters:
            if cluster.get('type') in ['circular_trading', 'ponzi_suspected', 'mixer_suspected']:
                if (node_id in cluster.get('cycle', []) or
                    node_id in cluster.get('pair', []) or
                    node_id in cluster.get('wallets', [])):
                    score += 30

        scores[node_id] = min(score, 100)

    return scores


def _classify_link_type(edge_data: Dict) -> str:
    """Determine link type from edge properties"""
    if 'type' in edge_data:
        return edge_data['type']

    # Infer from data
    if edge_data.get('method') and 'swap' in edge_data['method'].lower():
        return 'trade'

    return 'transfer'


def _calculate_risk_metrics(graph, clusters: List[Dict]) -> RiskMetricsModel:
    """Calculate overall risk metrics"""

    # Gini coefficient (wealth inequality)
    holdings = defaultdict(float)
    for source, target, data in graph.edges(data=True):
        holdings[target] += data.get('total_amount', 0)

    gini = _calculate_gini([v for v in holdings.values() if v > 0]) if holdings else 0

    # Wash trading score - count patterns and scale appropriately
    wash_count = len([c for c in clusters if c.get('type') in ['circular_trading', 'reciprocal_trading']])
    # Each pattern = 20 points, capped at 100
    wash_score = min(wash_count * 20, 100)

    # Mixer connections - each mixer connection is suspicious
    mixer_count = len([c for c in clusters if c.get('type') == 'mixer_suspected'])

    # Suspicious clusters - ponzi and common source patterns
    suspicious_count = len([c for c in clusters if c.get('type') in ['ponzi_suspected', 'common_source']])

    return RiskMetricsModel(
        giniCoefficient=gini,
        washTradingScore=wash_score,
        mixerConnectionsCount=mixer_count,
        suspiciousClustersDetected=suspicious_count
    )


def _calculate_gini(values: List[float]) -> float:
    """Calculate Gini coefficient"""
    if not values or len(values) < 2:
        return 0

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    cumsum = sum((i + 1) * val for i, val in enumerate(sorted_vals))
    return (2 * cumsum) / (n * sum(sorted_vals)) - (n + 1) / n


def _get_top_influential_wallets(graph, nodes: List[NodeModel], top_n: int = 10) -> List[TopInfluentialWallet]:
    """Extract top wallets by PageRank"""
    try:
        import networkx as nx
        pagerank = nx.pagerank(graph)
    except Exception as e:
        logger.warning(f"Could not calculate PageRank: {e}")
        pagerank = {}

    top_wallets = []
    for node_id, score in sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:top_n]:
        node = next((n for n in nodes if n.id == node_id), None)
        if node:
            # Classify risk level
            risk_score = node.riskScore or 0
            risk_level = (RiskLevel.LOW if risk_score < 30 else
                         RiskLevel.MEDIUM if risk_score < 60 else
                         RiskLevel.HIGH if risk_score < 80 else RiskLevel.CRITICAL)

            top_wallets.append(TopInfluentialWallet(
                address=node_id,
                pageRankScore=score,
                holdings=node.value,
                riskLevel=risk_level
            ))

    return top_wallets


def _extract_communities(clusters: List[Dict]) -> List[DetectedCommunity]:
    """Extract detected communities from clusters"""
    communities = []

    for i, cluster in enumerate(clusters):
        if cluster.get('type') in ['common_source', 'highly_connected', 'amount_based']:
            size = cluster.get('size', len(cluster.get('wallets', [])))
            suspicion = (RiskLevel.CRITICAL if size > 20 else
                        RiskLevel.HIGH if size > 10 else RiskLevel.MEDIUM)

            communities.append(DetectedCommunity(
                id=f"cluster_{i}",
                name=f"Cluster: {cluster.get('type').replace('_', ' ').title()}",
                walletCount=size,
                suspicionLevel=suspicion,
                description=f"Community of {size} wallets detected via {cluster.get('type')}"
            ))

    return communities


def _generate_red_flags(clusters: List[Dict]) -> List[RedFlag]:
    """Generate red flags from detected patterns"""
    flags = []

    severity_map = {
        'circular_trading': RiskLevel.CRITICAL,
        'ponzi_suspected': RiskLevel.CRITICAL,
        'mixer_suspected': RiskLevel.HIGH,
        'reciprocal_trading': RiskLevel.HIGH,
        'common_source': RiskLevel.MEDIUM,
        'wash_trading': RiskLevel.MEDIUM
    }

    for i, cluster in enumerate(clusters):
        cluster_type = cluster.get('type', 'unknown')
        severity = severity_map.get(cluster_type, RiskLevel.LOW)

        affected = (cluster.get('wallets', []) or
                   cluster.get('pair', []) or
                   cluster.get('cycle', []) or
                   cluster.get('funding_sources', []))

        if affected:
            flags.append(RedFlag(
                id=f"flag_{i}",
                severity=severity,
                title=cluster_type.replace('_', ' ').title(),
                description=f"Detected {cluster_type.replace('_', ' ')} pattern affecting {len(affected)} wallets",
                affectedWallets=affected[:10]  # Limit to first 10 for UI
            ))

    return flags


def _calculate_risk_score(metrics: RiskMetricsModel, red_flags: List[RedFlag]) -> float:
    """Calculate overall risk score (0-100) with proper weighting"""
    
    # Normalize each metric to 0-100
    gini_score = metrics.giniCoefficient * 100  # Gini is 0-1, scale to 0-100
    wash_score = min(metrics.washTradingScore, 100)  # Already 0-100
    mixer_score = min(metrics.mixerConnectionsCount * 15, 100)  # Scale mixer count
    suspicious_score = min(metrics.suspiciousClustersDetected * 10, 100)  # Scale cluster count
    
    # Red flags by severity
    critical_flags = len([f for f in red_flags if f.severity == RiskLevel.CRITICAL])
    high_flags = len([f for f in red_flags if f.severity == RiskLevel.HIGH])
    medium_flags = len([f for f in red_flags if f.severity == RiskLevel.MEDIUM])
    
    red_flag_score = (critical_flags * 25) + (high_flags * 15) + (medium_flags * 5)
    red_flag_score = min(red_flag_score, 100)
    
    # Weighted average of all components
    total_score = (
        gini_score * 0.20 +           # 20% - wealth concentration
        wash_score * 0.25 +           # 25% - wash trading patterns
        mixer_score * 0.15 +          # 15% - mixer connections
        suspicious_score * 0.15 +     # 15% - suspicious clusters
        red_flag_score * 0.25         # 25% - critical red flags
    )
    
    return min(total_score, 100)
