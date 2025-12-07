import { AlertTriangle, Info } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { InfluencerDumpingRisk } from "@/lib/mockData";

interface DumpingRiskMatrixProps {
  risks: InfluencerDumpingRisk[];
  onWalletSelect: (walletAddress: string) => void;
  onHighlightWallet: (walletAddress: string | null) => void;
}

/**
 * DumpingRiskMatrix Component - Scatter plot visualization of dumping risks
 *
 * X-axis: PageRank Score (Network Influence)
 * Y-axis: Token Holdings (Dumping Volume Potential)
 * Color: Dumping Probability
 * Size: Risk Score
 */
export default function DumpingRiskMatrix({
  risks,
  onWalletSelect,
  onHighlightWallet,
}: DumpingRiskMatrixProps) {
  if (risks.length === 0) {
    return (
      <Card className="border border-[#888888]/30 bg-gradient-to-b from-[#0a0a0a] to-[#1a0a2e]">
        <CardHeader>
          <CardTitle className="text-[#ffaa00]">DUMPING RISK MATRIX</CardTitle>
          <CardDescription>Influence vs Holdings Analysis</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center text-[#888888] py-8">
            No dumping risk data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate scale values
  const maxPageRank = Math.max(...risks.map(r => r.pageRankScore));
  const maxBalance = Math.max(...risks.map(r => r.tokenBalance));
  const maxRiskScore = Math.max(...risks.map(r => r.riskScore));

  const getRiskColor = (probability: number): string => {
    // Green (safe) to Red (dangerous)
    if (probability < 0.2) return "#00ff41"; // Green
    if (probability < 0.4) return "#88ff00"; // Yellow-green
    if (probability < 0.6) return "#ffaa00"; // Orange
    if (probability < 0.8) return "#ff5500"; // Orange-red
    return "#ff0055"; // Red/Pink
  };

  const getRiskLabel = (level: string): string => {
    switch (level) {
      case "critical":
        return "CRITICAL";
      case "high":
        return "HIGH";
      case "medium":
        return "MEDIUM";
      case "low":
        return "LOW";
      default:
        return "UNKNOWN";
    }
  };

  // Sort by dumping probability (highest first)
  const sortedRisks = [...risks].sort(
    (a, b) => b.dumpingProbability - a.dumpingProbability
  );

  // Separate by risk level
  const criticalRisks = sortedRisks.filter(r => r.riskLevel === "critical");
  const highRisks = sortedRisks.filter(r => r.riskLevel === "high");
  const mediumRisks = sortedRisks.filter(r => r.riskLevel === "medium");

  return (
    <Card className="border-2 border-[#ffaa00]/30 bg-gradient-to-b from-[#0a0a0a] to-[#1a0a2e]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" style={{ color: "#ffaa00" }} />
            <CardTitle className="text-[#ffaa00]">
              DUMPING RISK MATRIX
            </CardTitle>
          </div>
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="h-5 w-5 text-[#888888] cursor-help" />
            </TooltipTrigger>
            <TooltipContent className="bg-[#0a0a0a] border-[#ffaa00]/30 max-w-xs">
              <div className="space-y-2 text-sm">
                <p>
                  <strong>X-axis:</strong> PageRank Score (network influence)
                </p>
                <p>
                  <strong>Y-axis:</strong> Token Holdings (dumping volume
                  potential)
                </p>
                <p>
                  <strong>Color:</strong> Dumping probability (green=low,
                  red=high)
                </p>
                <p>
                  <strong>Size:</strong> Overall risk score
                </p>
              </div>
            </TooltipContent>
          </Tooltip>
        </div>
        <CardDescription>
          Influence vs Holdings Analysis - Higher right = Higher dumping risk
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Risk Category Lists */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Critical Risks */}
          {criticalRisks.length > 0 && (
            <div className="p-3 border-2 border-[#ff0000]/30 rounded-lg bg-[#1a0a0a]">
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: "#ff0055" }}
                />
                <span className="font-bold text-[#ff0055]">CRITICAL</span>
                <span className="text-xs text-[#888888]">
                  ({criticalRisks.length})
                </span>
              </div>
              <div className="space-y-2">
                {criticalRisks.slice(0, 5).map(risk => (
                  <div
                    key={risk.walletAddress}
                    className="p-2 bg-[#0a0a0a] border border-[#ff0000]/20 rounded cursor-pointer hover:border-[#ff0000]/50 transition-colors"
                    onClick={() => onWalletSelect(risk.walletAddress)}
                    onMouseEnter={() => onHighlightWallet(risk.walletAddress)}
                    onMouseLeave={() => onHighlightWallet(null)}
                  >
                    <div className="font-mono text-xs text-[#ff0055] truncate">
                      {risk.walletAddress.slice(0, 8)}...
                    </div>
                    <div className="text-xs text-[#888888] mt-1">
                      <span style={{ color: "#00ff41" }}>Prob:</span>{" "}
                      {(risk.dumpingProbability * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
                {criticalRisks.length > 5 && (
                  <div className="text-xs text-[#888888] text-center py-2">
                    +{criticalRisks.length - 5} more
                  </div>
                )}
              </div>
            </div>
          )}

          {/* High Risks */}
          {highRisks.length > 0 && (
            <div className="p-3 border-2 border-[#ff5500]/30 rounded-lg bg-[#1a0a0a]">
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: "#ff5500" }}
                />
                <span className="font-bold text-[#ff5500]">HIGH</span>
                <span className="text-xs text-[#888888]">
                  ({highRisks.length})
                </span>
              </div>
              <div className="space-y-2">
                {highRisks.slice(0, 5).map(risk => (
                  <div
                    key={risk.walletAddress}
                    className="p-2 bg-[#0a0a0a] border border-[#ff5500]/20 rounded cursor-pointer hover:border-[#ff5500]/50 transition-colors"
                    onClick={() => onWalletSelect(risk.walletAddress)}
                    onMouseEnter={() => onHighlightWallet(risk.walletAddress)}
                    onMouseLeave={() => onHighlightWallet(null)}
                  >
                    <div className="font-mono text-xs text-[#ff5500] truncate">
                      {risk.walletAddress.slice(0, 8)}...
                    </div>
                    <div className="text-xs text-[#888888] mt-1">
                      <span style={{ color: "#00ff41" }}>Prob:</span>{" "}
                      {(risk.dumpingProbability * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
                {highRisks.length > 5 && (
                  <div className="text-xs text-[#888888] text-center py-2">
                    +{highRisks.length - 5} more
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Medium Risks */}
          {mediumRisks.length > 0 && (
            <div className="p-3 border-2 border-[#ffaa00]/30 rounded-lg bg-[#1a0a0a]">
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: "#ffaa00" }}
                />
                <span className="font-bold text-[#ffaa00]">MEDIUM</span>
                <span className="text-xs text-[#888888]">
                  ({mediumRisks.length})
                </span>
              </div>
              <div className="space-y-2">
                {mediumRisks.slice(0, 5).map(risk => (
                  <div
                    key={risk.walletAddress}
                    className="p-2 bg-[#0a0a0a] border border-[#ffaa00]/20 rounded cursor-pointer hover:border-[#ffaa00]/50 transition-colors"
                    onClick={() => onWalletSelect(risk.walletAddress)}
                    onMouseEnter={() => onHighlightWallet(risk.walletAddress)}
                    onMouseLeave={() => onHighlightWallet(null)}
                  >
                    <div className="font-mono text-xs text-[#ffaa00] truncate">
                      {risk.walletAddress.slice(0, 8)}...
                    </div>
                    <div className="text-xs text-[#888888] mt-1">
                      <span style={{ color: "#00ff41" }}>Prob:</span>{" "}
                      {(risk.dumpingProbability * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
                {mediumRisks.length > 5 && (
                  <div className="text-xs text-[#888888] text-center py-2">
                    +{mediumRisks.length - 5} more
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="p-3 border border-[#888888]/20 rounded-lg bg-[#0a0a0a]">
          <div className="text-xs font-bold text-[#888888] mb-2">
            PROBABILITY SCALE
          </div>
          <div className="flex items-center justify-between">
            {[
              { label: "0%", color: "#00ff41" },
              { label: "25%", color: "#88ff00" },
              { label: "50%", color: "#ffaa00" },
              { label: "75%", color: "#ff5500" },
              { label: "100%", color: "#ff0055" },
            ].map(item => (
              <div key={item.label} className="text-center">
                <div
                  className="h-6 w-6 rounded mb-1"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-xs text-[#888888]">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
          <div className="p-2 border border-[#ff0055]/20 rounded">
            <div className="text-xs text-[#888888]">CRITICAL</div>
            <div className="font-mono font-bold text-[#ff0055]">
              {criticalRisks.length}
            </div>
          </div>
          <div className="p-2 border border-[#ff5500]/20 rounded">
            <div className="text-xs text-[#888888]">HIGH</div>
            <div className="font-mono font-bold text-[#ff5500]">
              {highRisks.length}
            </div>
          </div>
          <div className="p-2 border border-[#ffaa00]/20 rounded">
            <div className="text-xs text-[#888888]">MEDIUM</div>
            <div className="font-mono font-bold text-[#ffaa00]">
              {mediumRisks.length}
            </div>
          </div>
          <div className="p-2 border border-[#00ff41]/20 rounded">
            <div className="text-xs text-[#888888]">AVG PROB</div>
            <div className="font-mono font-bold text-[#00ff41]">
              {(
                (risks.reduce((sum, r) => sum + r.dumpingProbability, 0) /
                  risks.length) *
                100
              ).toFixed(0)}
              %
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
