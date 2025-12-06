import { X, AlertTriangle, TrendingUp, Network, Zap } from "lucide-react";
import type { Node, Link, AnalysisData } from "@/lib/mockData";

interface NodeDetailsModalProps {
  node: Node | null;
  data: AnalysisData | null;
  onClose: () => void;
}

/**
 * NodeDetailsModal - Shows detailed information about a selected wallet/node
 *
 * Displays:
 * - Node classification and risk score
 * - Holdings and transaction count
 * - Connected wallets (incoming/outgoing)
 * - Cluster memberships
 * - Red flags affecting this node
 */
export default function NodeDetailsModal({
  node,
  data,
  onClose,
}: NodeDetailsModalProps) {
  if (!node) return null;

  // Get node color based on type
  const getNodeTypeColor = (type: Node["group"]): string => {
    switch (type) {
      case "suspicious":
        return "#ff0055";
      case "mixer":
        return "#ff6600";
      case "deployer":
        return "#ffaa00";
      case "normal":
      default:
        return "#00ff41";
    }
  };

  // Get node type label
  const getNodeTypeLabel = (type: Node["group"]): string => {
    switch (type) {
      case "suspicious":
        return "SUSPICIOUS WALLET";
      case "mixer":
        return "MIXER/TUMBLER";
      case "deployer":
        return "TOKEN DEPLOYER";
      case "normal":
      default:
        return "NORMAL WALLET";
    }
  };

  // Get risk level color
  const getRiskColor = (score?: number): string => {
    if (!score) return "#00ff41";
    if (score < 30) return "#00ff41";
    if (score < 60) return "#ffaa00";
    return "#ff0055";
  };

  // Get risk level label
  const getRiskLabel = (score?: number): string => {
    if (!score) return "UNKNOWN";
    if (score < 30) return "LOW";
    if (score < 60) return "MEDIUM";
    return "HIGH/CRITICAL";
  };

  // Find connected nodes (incoming)
  const incomingLinks =
    data?.links.filter(link => link.target === node.id) || [];
  const outgoingLinks =
    data?.links.filter(link => link.source === node.id) || [];

  // Find communities containing this node
  const containingCommunities =
    data?.detectedCommunities.filter(comm =>
      data.nodes.some(
        n =>
          incomingLinks.some(l => l.source === n.id) ||
          outgoingLinks.some(l => l.target === n.id)
      )
    ) || [];

  // Find red flags affecting this node
  const affectingRedFlags =
    data?.redFlags.filter(flag => flag.affectedWallets.includes(node.id)) || [];

  // Find top influential wallets involving this node
  const nodeInInfluentials = data?.topInfluentialWallets.find(
    w => w.address === node.id
  );

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-dark-surface border border-neon-green/30 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto neon-shadow">
        {/* Header */}
        <div className="sticky top-0 bg-dark-bg border-b border-neon-green/30 p-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-bold text-neon-green flex items-center gap-2">
              <Network className="w-5 h-5" />
              {getNodeTypeLabel(node.group)}
            </h2>
            <p className="text-xs text-text-secondary mt-1 font-mono">
              {node.id}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-neon-green/10 rounded transition-colors"
          >
            <X className="w-5 h-5 text-neon-green" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {/* Risk Score */}
          <div className="bg-dark-bg/50 border border-neon-green/10 rounded p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-text-secondary tracking-widest">
                RISK SCORE
              </span>
              <span
                className="text-2xl font-bold"
                style={{ color: getRiskColor(node.riskScore) }}
              >
                {node.riskScore?.toFixed(1) || "N/A"}
              </span>
            </div>
            <div className="text-xs text-text-secondary">
              Status:{" "}
              <span style={{ color: getRiskColor(node.riskScore) }}>
                {getRiskLabel(node.riskScore)}
              </span>
            </div>
          </div>

          {/* Holdings & Transactions */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-dark-bg/50 border border-neon-green/10 rounded p-3">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="w-4 h-4 text-neon-green" />
                <span className="text-xs text-text-secondary tracking-widest">
                  HOLDINGS
                </span>
              </div>
              <p className="text-sm font-bold text-neon-green">
                {node.value.toLocaleString("en-US", {
                  maximumFractionDigits: 2,
                })}
              </p>
            </div>

            <div className="bg-dark-bg/50 border border-neon-green/10 rounded p-3">
              <div className="flex items-center gap-2 mb-1">
                <Zap className="w-4 h-4 text-neon-green" />
                <span className="text-xs text-text-secondary tracking-widest">
                  TRANSACTIONS
                </span>
              </div>
              <p className="text-sm font-bold text-neon-green">
                {node.transactions}
              </p>
            </div>
          </div>

          {/* Node Description */}
          {node.description && (
            <div className="bg-dark-bg/50 border border-neon-green/10 rounded p-3">
              <p className="text-xs text-text-secondary tracking-widest mb-2">
                DESCRIPTION
              </p>
              <p className="text-sm text-text-primary leading-relaxed">
                {node.description}
              </p>
            </div>
          )}

          {/* Top Influential Status */}
          {nodeInInfluentials && (
            <div className="bg-dark-bg/50 border border-orange-500/30 rounded p-3">
              <p className="text-xs text-orange-400 tracking-widest mb-2">
                🐋 TOP INFLUENTIAL WALLET
              </p>
              <p className="text-sm text-orange-300">
                PageRank Score:{" "}
                <span className="font-bold">
                  {nodeInInfluentials.pageRankScore.toFixed(4)}
                </span>
              </p>
            </div>
          )}

          {/* Incoming Connections */}
          {incomingLinks.length > 0 && (
            <div className="bg-dark-bg/50 border border-neon-green/10 rounded p-3">
              <p className="text-xs text-text-secondary tracking-widest mb-2">
                INCOMING TRANSFERS ({incomingLinks.length})
              </p>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {incomingLinks.slice(0, 5).map((link, idx) => {
                  const sourceNode = data?.nodes.find(
                    n => n.id === link.source
                  );
                  return (
                    <div
                      key={idx}
                      className="text-xs bg-dark-bg/50 p-2 rounded border border-neon-green/5"
                    >
                      <p className="text-text-secondary">
                        from:{" "}
                        <span className="text-neon-green font-mono">
                          {link.source.substring(0, 12)}...
                        </span>
                      </p>
                      <p className="text-text-primary">
                        Amount:{" "}
                        <span className="font-bold">
                          {link.value.toLocaleString("en-US", {
                            maximumFractionDigits: 2,
                          })}
                        </span>{" "}
                        ({link.count} tx)
                      </p>
                      {sourceNode && (
                        <p className="text-text-secondary text-xs">
                          Type:{" "}
                          <span className="text-neon-green">
                            {sourceNode.group.toUpperCase()}
                          </span>
                        </p>
                      )}
                    </div>
                  );
                })}
                {incomingLinks.length > 5 && (
                  <p className="text-xs text-text-secondary">
                    + {incomingLinks.length - 5} more
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Outgoing Connections */}
          {outgoingLinks.length > 0 && (
            <div className="bg-dark-bg/50 border border-neon-green/10 rounded p-3">
              <p className="text-xs text-text-secondary tracking-widest mb-2">
                OUTGOING TRANSFERS ({outgoingLinks.length})
              </p>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {outgoingLinks.slice(0, 5).map((link, idx) => {
                  const targetNode = data?.nodes.find(
                    n => n.id === link.target
                  );
                  return (
                    <div
                      key={idx}
                      className="text-xs bg-dark-bg/50 p-2 rounded border border-neon-green/5"
                    >
                      <p className="text-text-secondary">
                        to:{" "}
                        <span className="text-neon-green font-mono">
                          {link.target.substring(0, 12)}...
                        </span>
                      </p>
                      <p className="text-text-primary">
                        Amount:{" "}
                        <span className="font-bold">
                          {link.value.toLocaleString("en-US", {
                            maximumFractionDigits: 2,
                          })}
                        </span>{" "}
                        ({link.count} tx)
                      </p>
                      {targetNode && (
                        <p className="text-text-secondary text-xs">
                          Type:{" "}
                          <span className="text-neon-green">
                            {targetNode.group.toUpperCase()}
                          </span>
                        </p>
                      )}
                    </div>
                  );
                })}
                {outgoingLinks.length > 5 && (
                  <p className="text-xs text-text-secondary">
                    + {outgoingLinks.length - 5} more
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Red Flags */}
          {affectingRedFlags.length > 0 && (
            <div className="bg-dark-bg/50 border border-red-500/30 rounded p-3">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <p className="text-xs text-red-400 tracking-widest">
                  RED FLAGS ({affectingRedFlags.length})
                </p>
              </div>
              <div className="space-y-2">
                {affectingRedFlags.map((flag, idx) => (
                  <div
                    key={idx}
                    className="text-xs bg-dark-bg/50 p-2 rounded border border-red-500/20"
                  >
                    <p className="text-red-400 font-bold">{flag.title}</p>
                    <p className="text-text-secondary text-xs mt-1">
                      {flag.description}
                    </p>
                    <p className="text-text-secondary text-xs mt-1">
                      Severity:{" "}
                      <span className="text-red-400">
                        {flag.severity.toUpperCase()}
                      </span>
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Network Stats */}
          <div className="bg-dark-bg/50 border border-neon-green/10 rounded p-3">
            <p className="text-xs text-text-secondary tracking-widest mb-2">
              NETWORK STATS
            </p>
            <div className="space-y-1 text-xs">
              <p>
                In-Degree (incoming):{" "}
                <span className="text-neon-green font-bold">
                  {incomingLinks.length}
                </span>
              </p>
              <p>
                Out-Degree (outgoing):{" "}
                <span className="text-neon-green font-bold">
                  {outgoingLinks.length}
                </span>
              </p>
              <p>
                Total Connections:{" "}
                <span className="text-neon-green font-bold">
                  {incomingLinks.length + outgoingLinks.length}
                </span>
              </p>
              {nodeInInfluentials && (
                <p>
                  PageRank:{" "}
                  <span className="text-orange-400 font-bold">
                    {nodeInInfluentials.pageRankScore.toFixed(6)}
                  </span>
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
