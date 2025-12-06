"""CSV and JSON export service"""

import csv
import json
import logging
from io import StringIO
from app.schemas.graph import AnalysisDataModel

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting analysis results"""

    @staticmethod
    def export_to_csv(analysis_data: AnalysisDataModel) -> str:
        """
        Export analysis results to CSV format.

        Returns:
            CSV formatted string
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Blockchain Forensics Analysis Report"])
        writer.writerow([])

        # Summary
        writer.writerow(["Summary"])
        writer.writerow(["Overall Risk Score", f"{analysis_data.riskScore:.1f}"])
        writer.writerow(["Wallets Analyzed", len(analysis_data.nodes)])
        writer.writerow(["Transactions", len(analysis_data.links)])
        writer.writerow([])

        # Metrics
        writer.writerow(["Risk Metrics"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Gini Coefficient", f"{analysis_data.metrics.giniCoefficient:.3f}"])
        writer.writerow(["Wash Trading Score", f"{analysis_data.metrics.washTradingScore:.1f}%"])
        writer.writerow(["Mixer Connections", analysis_data.metrics.mixerConnectionsCount])
        writer.writerow(["Suspicious Clusters", analysis_data.metrics.suspiciousClustersDetected])
        writer.writerow([])

        # Top Wallets
        writer.writerow(["Top Influential Wallets"])
        writer.writerow(["Address", "PageRank Score", "Holdings", "Risk Level"])
        for wallet in analysis_data.topInfluentialWallets:
            writer.writerow([
                wallet.address,
                f"{wallet.pageRankScore:.6f}",
                f"{wallet.holdings:.2f}",
                wallet.riskLevel.value
            ])
        writer.writerow([])

        # Detected Communities
        writer.writerow(["Detected Communities"])
        writer.writerow(["Community", "Wallets", "Suspicion Level", "Description"])
        for community in analysis_data.detectedCommunities:
            writer.writerow([
                community.name,
                community.walletCount,
                community.suspicionLevel.value,
                community.description
            ])
        writer.writerow([])

        # Red Flags
        writer.writerow(["Red Flags / Alerts"])
        writer.writerow(["ID", "Severity", "Title", "Description", "Affected Wallets"])
        for flag in analysis_data.redFlags:
            writer.writerow([
                flag.id,
                flag.severity.value,
                flag.title,
                flag.description,
                "; ".join(flag.affectedWallets[:3])
            ])
        writer.writerow([])

        # Nodes
        writer.writerow(["Analyzed Wallets"])
        writer.writerow(["Address", "Label", "Type", "Holdings", "Transactions", "Risk Score"])
        for node in analysis_data.nodes:
            writer.writerow([
                node.id,
                node.label,
                node.group.value,
                f"{node.value:.2f}",
                node.transactions,
                f"{node.riskScore:.1f}" if node.riskScore else "N/A"
            ])

        return output.getvalue()

    @staticmethod
    def export_to_json(analysis_data: AnalysisDataModel) -> str:
        """
        Export analysis results to JSON format.

        Returns:
            JSON formatted string
        """
        return analysis_data.model_dump_json(indent=2)
