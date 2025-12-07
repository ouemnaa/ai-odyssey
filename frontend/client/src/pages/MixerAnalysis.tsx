import { useState } from "react";
import { AlertTriangle, Zap } from "lucide-react";
import { Toaster, toast } from "sonner";
import Header from "@/components/Header";
import SearchSection from "@/components/SearchSection";
import MixerAnalysisPanel from "@/components/MixerAnalysisPanel";
import { useLocation } from "wouter";
import * as analysisService from "@/services/analysisService";

/**
 * Mixer Detection Analysis Page
 *
 * Displays first-flow agent analysis:
 * - AI-generated mixer detection report
 * - Mixer network visualization
 * - Wallet exposure assessment
 */
export default function MixerAnalysis() {
  const [, setLocation] = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTokenAddress, setSelectedTokenAddress] = useState("");
  const [mixerResult, setMixerResult] = useState<any>(null);
  const [analysisTime, setAnalysisTime] = useState<number>(0);

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
    const startTime = Date.now();

    try {
      toast.loading("Analyzing token for mixer connections...");

      const response = await analysisService.analyzeMixers(tokenAddress, 3);

      if (response.status === "success") {
        setMixerResult(response.result);
        const duration = (Date.now() - startTime) / 1000;
        setAnalysisTime(duration);

        toast.success(
          `Mixer analysis complete in ${duration.toFixed(2)}s - ${response.result.summary.mixersDetected} mixers detected`
        );
      } else {
        toast.error("Mixer analysis failed");
      }
    } catch (error) {
      console.error("Analysis error:", error);
      toast.error(`Failed to analyze token: ${String(error)}`);
    } finally {
      setIsLoading(false);
    }
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

        {!mixerResult ? (
          // Initial state / Landing view
          <div className="min-h-screen flex flex-col items-center justify-center px-4">
            <div className="max-w-2xl w-full space-y-12">
              {/* Hero Section */}
              <div className="text-center space-y-6">
                <div className="space-y-2">
                  <h1 className="text-5xl md:text-6xl font-bold text-neon-green">
                    MIXER DETECTION
                  </h1>
                  <p className="text-xl text-text-secondary">
                    Privacy Mixer Analysis & Risk Assessment
                  </p>
                </div>

                <p className="text-text-secondary text-lg leading-relaxed">
                  Detect Tornado Cash and other privacy mixers. Identify wallets
                  with mixer exposure and assess financial risk through advanced
                  heuristics analysis.
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
                  {[
                    {
                      name: "USDT",
                      address: "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                    },
                    {
                      name: "USDC",
                      address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    },
                    {
                      name: "DAI",
                      address: "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    },
                  ].map(token => (
                    <button
                      key={token.address}
                      onClick={() => handleAnalyze(token.address)}
                      disabled={isLoading}
                      className="neon-card hover:bg-dark-bg/50 text-left transition-all duration-200 disabled:opacity-50"
                    >
                      <div className="space-y-2">
                        <p className="font-bold text-neon-green">
                          {token.name}
                        </p>
                        <p className="text-xs text-text-secondary font-mono">
                          {token.address.substring(0, 20)}...
                        </p>
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
                        Mixer Detection
                      </h3>
                      <p className="text-xs text-text-secondary">
                        Identify privacy mixers using behavioral heuristics
                      </p>
                    </div>
                  </div>
                </div>

                <div className="neon-card">
                  <div className="flex gap-3">
                    <Zap className="w-5 h-5 text-neon-green flex-shrink-0" />
                    <div>
                      <h3 className="font-bold text-neon-green mb-1">
                        Risk Assessment
                      </h3>
                      <p className="text-xs text-text-secondary">
                        Evaluate wallet exposure to mixer connections
                      </p>
                    </div>
                  </div>
                </div>

                <div className="neon-card">
                  <div className="flex gap-3">
                    <AlertTriangle className="w-5 h-5 text-neon-orange flex-shrink-0" />
                    <div>
                      <h3 className="font-bold text-neon-green mb-1">
                        Provenance Tracing
                      </h3>
                      <p className="text-xs text-text-secondary">
                        Trace mixer exposure up to 3 hops in transaction chain
                      </p>
                    </div>
                  </div>
                </div>

                <div className="neon-card">
                  <div className="flex gap-3">
                    <Zap className="w-5 h-5 text-neon-cyan flex-shrink-0" />
                    <div>
                      <h3 className="font-bold text-neon-green mb-1">
                        Network Analysis
                      </h3>
                      <p className="text-xs text-text-secondary">
                        Understand mixer network topology and connections
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Info Box */}
              <div className="neon-card bg-dark-bg/50 border-neon-green/30 p-4 text-center text-xs text-text-secondary">
                <p>
                  ⚡{" "}
                  <span className="text-neon-green font-bold">
                    Fast Analysis:
                  </span>{" "}
                  Typically completes in 8-15 seconds
                </p>
                <p className="mt-2">
                  📊{" "}
                  <span className="text-neon-green font-bold">
                    Up to 10,000
                  </span>{" "}
                  transactions analyzed per token
                </p>
              </div>
            </div>
          </div>
        ) : (
          // Results view
          <div className="p-4 md:p-6">
            {/* Back button and header */}
            <div className="mb-6 flex items-center justify-between">
              <button
                onClick={() => {
                  setMixerResult(null);
                  setSelectedTokenAddress("");
                }}
                className="text-neon-green hover:text-neon-cyan transition-colors"
              >
                ← Back to Search
              </button>
              <div className="text-right">
                <p className="text-xs text-text-secondary">Analysis Time</p>
                <p className="text-sm font-bold text-neon-green">
                  {analysisTime.toFixed(2)}s
                </p>
              </div>
            </div>

            {/* Mixer Analysis Results */}
            <MixerAnalysisPanel
              textReport={mixerResult.textReport || ""}
              graphData={
                mixerResult.graphData || {
                  nodes: [],
                  edges: [],
                  statistics: {},
                }
              }
              summary={mixerResult.summary || {}}
            />
          </div>
        )}
      </div>
    </div>
  );
}
