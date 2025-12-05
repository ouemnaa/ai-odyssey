import { useState } from "react";
import { Search, Zap, AlertTriangle } from "lucide-react";
import { Toaster, toast } from "sonner";
import Header from "@/components/Header";
import SearchSection from "@/components/SearchSection";
import GraphVisualization from "@/components/GraphVisualization";
import RiskDashboard from "@/components/RiskDashboard";
import AnalysisResults from "@/components/AnalysisResults";
import { generateMockData, SAMPLE_TOKENS } from "@/lib/mockData";
import type { AnalysisData } from "@/lib/mockData";

/**
 * BlockStat Forensic Graph Agent - Main Application
 *
 * Design Philosophy: Classic Matrix Cyberpunk
 * - Pure black background (#000000) with neon green accents (#00ff41)
 * - Monospace typography for terminal/hacker aesthetic
 * - Glow effects and animations for digital feel
 * - Information-dense layout with minimal padding
 */
export default function Home() {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTokenAddress, setSelectedTokenAddress] = useState("");
  const [highlightedWallet, setHighlightedWallet] = useState<string | null>(
    null
  );

  const handleAnalyze = async (tokenAddress: string) => {
    if (!tokenAddress.trim()) {
      toast.error("Please enter a valid token contract address");
      return;
    }

    setSelectedTokenAddress(tokenAddress);
    setIsLoading(true);
    toast.loading("Analyzing token forensics...");

    // Simulate API call delay
    setTimeout(() => {
      const data = generateMockData(tokenAddress);
      setAnalysisData(data);
      setIsLoading(false);
      toast.success("Analysis complete - forensic graph loaded");
    }, 2000);
  };

  const handleSampleTokenClick = (address: string) => {
    handleAnalyze(address);
  };

  const handleWalletHighlight = (walletId: string | null) => {
    setHighlightedWallet(walletId);
  };

  return (
    <div className="min-h-screen bg-dark-bg text-text-primary overflow-hidden">
      <Toaster theme="dark" position="bottom-right" />

      {/* Background scanline effect */}
      <div className="fixed inset-0 pointer-events-none opacity-5">
        <div className="absolute inset-0 scanline"></div>
      </div>

      {/* Main content */}
      <div className="relative z-10">
        <Header />

        {!analysisData ? (
          // Initial state / Landing view
          <div className="min-h-screen flex flex-col items-center justify-center px-4">
            <div className="max-w-2xl w-full space-y-12">
              {/* Hero Section */}
              <div className="text-center space-y-6">
                <div className="space-y-2">
                  <h1 className="text-5xl md:text-6xl font-bold text-neon-green">
                    FORENSIC GRAPH AGENT
                  </h1>
                  <p className="text-xl text-text-secondary">
                    Vision in the Dark Forest
                  </p>
                </div>

                <p className="text-text-secondary text-lg leading-relaxed">
                  Detect cryptocurrency fraud with advanced graph analysis.
                  Identify wash trading patterns, mixer connections, and
                  suspicious wallet clusters in real-time.
                </p>
              </div>

              {/* Search Section */}
              <SearchSection
                onAnalyze={handleAnalyze}
                isLoading={isLoading}
                selectedTokenAddress={selectedTokenAddress}
                onTokenAddressChange={setSelectedTokenAddress}
              />

              {/* Sample Tokens */}
              <div className="space-y-4">
                <p className="text-center text-text-secondary text-sm">
                  Or try a sample token:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {SAMPLE_TOKENS.map(token => (
                    <button
                      key={token.address}
                      onClick={() => handleSampleTokenClick(token.address)}
                      className="neon-card hover:bg-dark-bg/50 text-left transition-all duration-200"
                    >
                      <div className="flex items-start gap-2">
                        <Zap className="w-4 h-4 text-neon-green flex-shrink-0 mt-1" />
                        <div className="min-w-0">
                          <p className="font-semibold text-neon-green text-sm">
                            {token.name}
                          </p>
                          <p className="text-xs text-text-secondary truncate font-mono">
                            {token.address}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Features Overview */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-8">
                <div className="neon-card">
                  <div className="flex gap-3">
                    <AlertTriangle className="w-5 h-5 text-neon-pink flex-shrink-0" />
                    <div>
                      <h3 className="font-bold text-neon-green mb-1">
                        Red Flag Detection
                      </h3>
                      <p className="text-xs text-text-secondary">
                        Identify suspicious patterns and malicious activity
                      </p>
                    </div>
                  </div>
                </div>

                <div className="neon-card">
                  <div className="flex gap-3">
                    <Search className="w-5 h-5 text-neon-green flex-shrink-0" />
                    <div>
                      <h3 className="font-bold text-neon-green mb-1">
                        Graph Analysis
                      </h3>
                      <p className="text-xs text-text-secondary">
                        Visualize wallet networks and transaction flows
                      </p>
                    </div>
                  </div>
                </div>

                <div className="neon-card">
                  <div className="flex gap-3">
                    <Zap className="w-5 h-5 text-neon-cyan flex-shrink-0" />
                    <div>
                      <h3 className="font-bold text-neon-green mb-1">
                        Risk Scoring
                      </h3>
                      <p className="text-xs text-text-secondary">
                        Comprehensive risk assessment with detailed metrics
                      </p>
                    </div>
                  </div>
                </div>

                <div className="neon-card">
                  <div className="flex gap-3">
                    <AlertTriangle className="w-5 h-5 text-neon-cyan flex-shrink-0" />
                    <div>
                      <h3 className="font-bold text-neon-green mb-1">
                        Community Detection
                      </h3>
                      <p className="text-xs text-text-secondary">
                        Discover coordinated wallet clusters and rings
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Analysis view
          <div className="space-y-6 p-4 md:p-6">
            {/* Search bar (sticky at top) */}
            <div className="sticky top-0 z-20 bg-dark-bg/95 py-4 -mx-4 md:-mx-6 px-4 md:px-6 border-b border-neon-green/20">
              <SearchSection
                onAnalyze={handleAnalyze}
                isLoading={isLoading}
                selectedTokenAddress={selectedTokenAddress}
                onTokenAddressChange={setSelectedTokenAddress}
              />
            </div>

            {/* Main analysis layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Graph visualization - main area */}
              <div className="lg:col-span-2">
                <GraphVisualization
                  data={analysisData}
                  highlightedWallet={highlightedWallet}
                  onWalletSelect={handleWalletHighlight}
                />
              </div>

              {/* Risk dashboard - sidebar */}
              <div className="lg:col-span-1">
                <RiskDashboard
                  data={analysisData}
                  onWalletHighlight={handleWalletHighlight}
                />
              </div>
            </div>

            {/* Analysis results - full width */}
            <AnalysisResults
              data={analysisData}
              onWalletHighlight={handleWalletHighlight}
            />
          </div>
        )}
      </div>
    </div>
  );
}
