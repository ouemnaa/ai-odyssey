import { TrendingUp, Zap, AlertTriangle, Users } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { PageRankMetrics, InfluencerDumpingRisk } from "@/lib/mockData";

interface InfluencerPanelProps {
  topInfluencers: PageRankMetrics[];
  dumpingRisks: InfluencerDumpingRisk[];
  onWalletSelect: (walletAddress: string) => void;
  onHighlightWallet: (walletAddress: string | null) => void;
}

/**
 * InfluencerPanel Component - Displays PageRank analysis results
 *
 * Features:
 * - Top influential wallets ranked by PageRank score
 * - Whale indicators and holdings information
 * - Network connectivity metrics (in/out degree)
 * - Dumping risk assessment with color-coding
 * - Interactive highlighting in graph visualization
 */
export default function InfluencerPanel({
  topInfluencers,
  dumpingRisks,
  onWalletSelect,
  onHighlightWallet,
}: InfluencerPanelProps) {
  const getInfluenceColor = (level: string): string => {
    switch (level) {
      case "very_high":
        return "#ff00ff"; // Magenta
      case "high":
        return "#ff0055"; // Pink
      case "medium":
        return "#ffaa00"; // Orange
      case "low":
        return "#00ff41"; // Green
      default:
        return "#888888"; // Gray
    }
  };

  const getRiskColor = (level: string): string => {
    switch (level) {
      case "critical":
        return "#ff0000"; // Red
      case "high":
        return "#ff5500"; // Orange-red
      case "medium":
        return "#ffaa00"; // Orange
      case "low":
        return "#00ff41"; // Green
      default:
        return "#888888";
    }
  };

  const getInfluenceBadgeVariant = (level: string) => {
    switch (level) {
      case "very_high":
      case "high":
        return "destructive";
      case "medium":
        return "secondary";
      default:
        return "outline";
    }
  };

  const getRiskBadgeVariant = (level: string) => {
    switch (level) {
      case "critical":
      case "high":
        return "destructive";
      case "medium":
        return "secondary";
      default:
        return "outline";
    }
  };

  // Find dumping risks for each influencer
  const getInfluencerRisk = (
    address: string
  ): InfluencerDumpingRisk | undefined => {
    return dumpingRisks.find(
      risk => risk.walletAddress.toLowerCase() === address.toLowerCase()
    );
  };

  return (
    <div className="space-y-4">
      {/* Top Influencers Section */}
      <Card className="border-2 border-[#ff00ff]/30 bg-gradient-to-b from-[#0a0a0a] to-[#1a0a2e]">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" style={{ color: "#ff00ff" }} />
              <CardTitle className="text-[#ff00ff]">TOP INFLUENCERS</CardTitle>
            </div>
            <CardDescription>{topInfluencers.length} analyzed</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {topInfluencers.length === 0 ? (
            <div className="text-center text-[#888888] py-6">
              No influencer data available
            </div>
          ) : (
            topInfluencers.map((influencer, index) => {
              const risk = getInfluencerRisk(influencer.walletAddress);
              const shortAddr = `${influencer.walletAddress.slice(0, 6)}...${influencer.walletAddress.slice(-4)}`;

              return (
                <div
                  key={influencer.walletAddress}
                  className="p-3 border border-[#ff00ff]/20 rounded-lg hover:border-[#ff00ff]/50 hover:bg-[#1a0a2e] transition-colors cursor-pointer"
                  onClick={() => onWalletSelect(influencer.walletAddress)}
                  onMouseEnter={() =>
                    onHighlightWallet(influencer.walletAddress)
                  }
                  onMouseLeave={() => onHighlightWallet(null)}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 flex-1">
                      <span className="font-mono text-[#00ff41] font-bold w-6">
                        {index + 1}.
                      </span>
                      <div className="flex flex-col gap-1 flex-1">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="font-mono text-sm text-[#ff00ff] hover:text-[#ff00ff]/80 truncate">
                              {shortAddr}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent
                            side="right"
                            className="bg-[#0a0a0a] border-[#ff00ff]/30"
                          >
                            {influencer.walletAddress}
                          </TooltipContent>
                        </Tooltip>
                        <div className="flex gap-2 text-xs">
                          {influencer.isWhale && (
                            <Tooltip>
                              <TooltipTrigger>
                                <span className="text-xl">🐋</span>
                              </TooltipTrigger>
                              <TooltipContent className="bg-[#0a0a0a] border-[#ff00ff]/30">
                                Major Token Holder
                              </TooltipContent>
                            </Tooltip>
                          )}
                          <Badge
                            variant={getInfluenceBadgeVariant(
                              influencer.influence
                            )}
                            className="text-xs"
                          >
                            {influencer.influence.toUpperCase()}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div
                        className="font-mono font-bold text-sm"
                        style={{
                          color: getInfluenceColor(influencer.influence),
                        }}
                      >
                        {influencer.pageRankScore.toFixed(4)}
                      </div>
                      <div className="text-xs text-[#888888]">PageRank</div>
                    </div>
                  </div>

                  {/* Metrics Row */}
                  <div className="grid grid-cols-3 gap-2 text-xs text-[#888888] mb-2 px-1">
                    <div>
                      <span className="text-[#00ff41]">IN:</span>{" "}
                      {influencer.inDegree}
                    </div>
                    <div>
                      <span className="text-[#ff00ff]">OUT:</span>{" "}
                      {influencer.outDegree}
                    </div>
                    <div>
                      <span className="text-[#ffaa00]">BAL:</span>{" "}
                      {(influencer.tokenBalance / 1e6).toFixed(1)}M
                    </div>
                  </div>

                  {/* Dumping Risk Indicator */}
                  {risk && (
                    <div className="pt-2 border-t border-[#ff00ff]/20">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <AlertTriangle
                            className="h-4 w-4"
                            style={{ color: getRiskColor(risk.riskLevel) }}
                          />
                          <span className="text-xs font-mono">Dump Risk:</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div
                            className="w-12 h-1 rounded-full bg-[#333]"
                            style={{
                              background: `linear-gradient(to right, #00ff41, #ffaa00, #ff0055)`,
                            }}
                          >
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${risk.dumpingProbability * 100}%`,
                                backgroundColor: getRiskColor(risk.riskLevel),
                              }}
                            />
                          </div>
                          <span
                            className="text-xs font-mono font-bold"
                            style={{ color: getRiskColor(risk.riskLevel) }}
                          >
                            {(risk.dumpingProbability * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <Badge
                        variant={getRiskBadgeVariant(risk.riskLevel)}
                        className="text-xs mt-1"
                      >
                        {risk.riskLevel.toUpperCase()}
                      </Badge>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </CardContent>
      </Card>

      {/* Network Statistics */}
      {topInfluencers.length > 0 && (
        <Card className="border border-[#888888]/30 bg-gradient-to-b from-[#0a0a0a] to-[#1a0a2e]">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5" style={{ color: "#00ff41" }} />
              <CardTitle className="text-[#00ff41]">NETWORK INSIGHTS</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4 text-sm">
            <div className="p-2 border border-[#00ff41]/20 rounded">
              <div className="text-[#888888] text-xs mb-1">AVG INFLUENCE</div>
              <div
                className="font-mono font-bold"
                style={{
                  color: "#00ff41",
                }}
              >
                {(
                  topInfluencers.reduce((sum, i) => sum + i.pageRankScore, 0) /
                  topInfluencers.length
                ).toFixed(4)}
              </div>
            </div>
            <div className="p-2 border border-[#ff00ff]/20 rounded">
              <div className="text-[#888888] text-xs mb-1">MAX CONNECTIONS</div>
              <div
                className="font-mono font-bold"
                style={{
                  color: "#ff00ff",
                }}
              >
                {Math.max(...topInfluencers.map(i => i.inDegree + i.outDegree))}
              </div>
            </div>
            <div className="p-2 border border-[#ffaa00]/20 rounded">
              <div className="text-[#888888] text-xs mb-1">TOTAL HOLDINGS</div>
              <div
                className="font-mono font-bold"
                style={{
                  color: "#ffaa00",
                }}
              >
                {(
                  topInfluencers.reduce((sum, i) => sum + i.tokenBalance, 0) /
                  1e9
                ).toFixed(1)}
                B
              </div>
            </div>
            <div className="p-2 border border-[#ff0055]/20 rounded">
              <div className="text-[#888888] text-xs mb-1">HIGH RISK</div>
              <div
                className="font-mono font-bold"
                style={{
                  color: "#ff0055",
                }}
              >
                {
                  dumpingRisks.filter(
                    r => r.riskLevel === "high" || r.riskLevel === "critical"
                  ).length
                }
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
