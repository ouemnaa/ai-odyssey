import { useState, useEffect } from "react";
import { Search, Zap, AlertTriangle } from "lucide-react";
import { Toaster, toast } from "sonner";
import Header from "@/components/Header";
import SearchSection from "@/components/SearchSection";
import GraphVisualization from "@/components/GraphVisualization";
import RiskDashboard from "@/components/RiskDashboard";
import AnalysisResults from "@/components/AnalysisResults";
import NodeDetailsModal from "@/components/NodeDetailsModal";
import { generateMockData, SAMPLE_TOKENS } from "@/lib/mockData";
import type { AnalysisData, Node } from "@/lib/mockData";
import * as analysisService from "@/services/analysisService";

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
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [currentAnalysisId, setCurrentAnalysisId] = useState<string | null>(
    null
  );
  const [analysisTimings, setAnalysisTimings] = useState<
    Record<string, string>
  >({});

  // Check if backend is available on mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const isHealthy = await analysisService.healthCheck();
      setBackendAvailable(isHealthy);
      if (!isHealthy) {
        console.warn("Backend not available, falling back to mock data");
      }
    } catch (error) {
      console.warn("Backend health check failed:", error);
      setBackendAvailable(false);
    }
  };

  const pollAnalysisStatus = async (analysisId: string) => {
    try {
      const maxAttempts = 600; // 10 minutes with 1 second intervals
      let attempts = 0;

      while (attempts < maxAttempts) {
        const status = await analysisService.checkAnalysisStatus(analysisId);

        // Update progress with timing info
        let toastMessage = `Analyzing... ${status.progress}% - ${status.currentStep}`;
        if (status.totalDuration) {
          toastMessage += ` [${status.totalDuration}]`;
        }
        toast.loading(toastMessage);

        // Store step timings for display
        if (status.stepTimings) {
          setAnalysisTimings(status.stepTimings);
        }

        if (status.status === "completed") {
          // Fetch the results
          const results = await analysisService.getAnalysisResults(analysisId);
          setAnalysisData(results as any);
          setCurrentAnalysisId(analysisId);

          // Display final timings
          const timingsSummary = status.stepTimings
            ? Object.entries(status.stepTimings)
                .map(([step, time]) => `${step}: ${time}`)
                .join(" | ")
            : "";

          if (timingsSummary) {
            toast.success(
              `Analysis complete in ${status.totalDuration}! Timings: ${timingsSummary}`
            );
          } else {
            toast.success("Analysis complete! Forensic graph loaded.");
          }
          return;
        } else if (status.status === "failed") {
          toast.error(`Analysis failed: ${status.errorMessage}`);
          setIsLoading(false);
          return;
        }

        // Wait 1 second before next poll
        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;
      }

      toast.error("Analysis timeout - please try again");
      setIsLoading(false);
    } catch (error) {
      console.error("Error polling status:", error);
      toast.error("Failed to poll analysis status");
      setIsLoading(false);
    }
  };

  const handleAnalyze = async (tokenAddress: string) => {
    if (!tokenAddress.trim()) {
      toast.error("Please enter a valid token contract address");
      return;
    }

    if (!tokenAddress.startsWith("0x") || tokenAddress.length !== 42) {
      toast.error(
        "Invalid token address format (should be 0x followed by 40 hex characters)"
      );
      return;
    }

    setSelectedTokenAddress(tokenAddress);
    setIsLoading(true);

    try {
      if (backendAvailable) {
        // Use real backend API
        toast.loading("Submitting analysis to backend...");
        const response = await analysisService.submitAnalysis({
          tokenAddress,
          daysBack: 7,
          sampleSize: 5000,
        });

        toast.loading("Analysis queued... waiting for results");
        setCurrentAnalysisId(response.analysisId);
        await pollAnalysisStatus(response.analysisId);
      } else {
        // Fallback to mock data
        toast.loading("Using mock data (backend unavailable)...");
        setTimeout(() => {
          const data = generateMockData(tokenAddress);
          setAnalysisData(data);
          setIsLoading(false);
          toast.success("Mock analysis complete - forensic graph loaded");
        }, 2000);
      }
    } catch (error) {
      console.error("Analysis error:", error);

      // Fallback to mock data on error
      if (backendAvailable) {
        toast.info("Backend error - falling back to mock data");
        const data = generateMockData(tokenAddress);
        setAnalysisData(data);
        setIsLoading(false);
      } else {
        toast.error("Analysis failed and backend is unavailable");
        setIsLoading(false);
      }
    }
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
              {/* Loading with timings display */}
              {isLoading && Object.keys(analysisTimings).length > 0 && (
                <div className="fixed top-20 right-4 bg-dark-bg border border-neon-green/50 rounded p-4 max-w-sm text-sm">
                  <p className="text-neon-green font-bold mb-2">
                    ⏱️ Analysis Timings:
                  </p>
                  <div className="space-y-1 text-text-secondary">
                    {Object.entries(analysisTimings).map(([step, time]) => (
                      <div key={step} className="flex justify-between gap-2">
                        <span>{step.replace(/_/g, " ")}:</span>
                        <span className="text-neon-green">{time}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
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
                  onNodeClick={setSelectedNode}
                />
              </div>

              {/* Risk dashboard - sidebar */}
              <div className="lg:col-span-1">
                <RiskDashboard
                  data={analysisData}
                  onWalletHighlight={handleWalletHighlight}
                  timings={analysisTimings}
                />
              </div>
            </div>

            {/* Analysis results - full width */}
            <AnalysisResults
              data={analysisData}
              onWalletHighlight={handleWalletHighlight}
            />

            {/* Node Details Modal */}
            <NodeDetailsModal
              node={selectedNode}
              data={analysisData}
              onClose={() => setSelectedNode(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
