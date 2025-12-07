import { useState } from "react";
import { AlertTriangle, Activity, Users, Network } from "lucide-react";
import MixerGraphVisualization from "./MixerGraphVisualization";
import MarkdownRenderer from "./MarkdownRenderer";
import type { AnalysisData } from "@/lib/mockData";

interface MixerAnalysisPanelProps {
  textReport: string;
  graphData: {
    nodes: Array<any>;
    edges: Array<any>;
    statistics: Record<string, any>;
  };
  summary: {
    tokenAddress: string;
    analysisTime: string;
    timestamp: string;
    mixersDetected: number;
    walletsExposed: number;
  };
}

/**
 * MixerAnalysisPanel Component
 *
 * Displays:
 * 1. AI-generated text report (description under graph)
 * 2. Graph visualization with mixer nodes and wallet connections
 * 3. Summary statistics
 */
export default function MixerAnalysisPanel({
  textReport,
  graphData,
  summary,
}: MixerAnalysisPanelProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  // Parse markdown headers from text report
  const parseReportSections = (text: string) => {
    const lines = text.split("\n");
    const sections: Array<{ title: string; content: string[] }> = [];
    let currentSection: { title: string; content: string[] } = {
      title: "",
      content: [],
    };

    for (const line of lines) {
      if (line.startsWith("### *")) {
        if (currentSection.title) {
          sections.push({ ...currentSection });
        }
        currentSection = {
          title: line.replace("### *", "").replace("*", ""),
          content: [],
        };
      } else if (line.startsWith("**") && line.includes(":")) {
        currentSection.content.push(line);
      } else if (line.trim() && !line.startsWith("---")) {
        currentSection.content.push(line);
      }
    }

    if (currentSection.title) {
      sections.push({ ...currentSection });
    }

    return sections;
  };

  const sections = parseReportSections(textReport);
  const stats = graphData.statistics;

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="neon-card p-3 text-center">
          <div className="text-xs text-text-secondary mb-1 tracking-widest">
            MIXERS DETECTED
          </div>
          <div className="text-2xl font-bold text-neon-pink">
            {summary.mixersDetected}
          </div>
        </div>
        <div className="neon-card p-3 text-center">
          <div className="text-xs text-text-secondary mb-1 tracking-widest">
            WALLETS EXPOSED
          </div>
          <div className="text-2xl font-bold text-neon-orange">
            {summary.walletsExposed}
          </div>
        </div>
        <div className="neon-card p-3 text-center">
          <div className="text-xs text-text-secondary mb-1 tracking-widest">
            ANALYSIS TIME
          </div>
          <div className="text-lg font-bold text-neon-green">
            {summary.analysisTime}
          </div>
        </div>
        <div className="neon-card p-3 text-center">
          <div className="text-xs text-text-secondary mb-1 tracking-widest">
            GRAPH NODES
          </div>
          <div className="text-2xl font-bold text-neon-cyan">
            {graphData.nodes?.length || 0}
          </div>
        </div>
      </div>

      {/* Graph Visualization */}
      <div className="neon-card overflow-hidden" style={{ height: "500px" }}>
        <MixerGraphVisualization
          data={{
            nodes: graphData.nodes || [],
            edges: graphData.edges || [],
            statistics: graphData.statistics || {},
          }}
        />
      </div>

      {/* Mixer Detection Report - Collapsible Sections */}
      <div className="neon-card p-4 space-y-2">
        <h2 className="text-lg font-bold text-neon-green tracking-widest">
          🔍 MIXER DETECTION REPORT
        </h2>

        {sections.map((section, idx) => (
          <div
            key={idx}
            className="border-b border-neon-green/20 last:border-b-0"
          >
            <button
              onClick={() => toggleSection(section.title)}
              className="w-full flex justify-between items-center py-2 hover:bg-dark-bg/50 transition-colors"
            >
              <span className="text-sm font-bold text-neon-green">
                ▸ {section.title}
              </span>
              <span className="text-xs text-text-secondary">
                {expandedSection === section.title ? "▼" : "▶"}
              </span>
            </button>

            {expandedSection === section.title && (
              <div className="pl-4 pb-3 space-y-1 text-xs text-text-secondary font-mono">
                {section.content.map((line, lineIdx) => (
                  <div key={lineIdx} className="text-text-secondary">
                    {line}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Network Statistics */}
      {stats.networkStats && Object.keys(stats.networkStats).length > 0 && (
        <div className="neon-card p-4">
          <h3 className="text-sm font-bold text-neon-cyan mb-3 tracking-widest">
            📊 NETWORK STATISTICS
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            {Object.entries(stats.networkStats).map(([key, value]) => (
              <div key={key} className="bg-dark-bg/50 p-2 rounded">
                <div className="text-text-secondary capitalize">
                  {key.replace(/_/g, " ")}
                </div>
                <div className="text-neon-green font-bold">
                  {String(value).substring(0, 20)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Full Report with Markdown Rendering */}
      <div className="neon-card p-4">
        <button
          onClick={() => toggleSection("full-report")}
          className="w-full flex justify-between items-center mb-3"
        >
          <span className="text-sm font-bold text-neon-cyan tracking-widest">
            📄 DETAILED ANALYSIS REPORT
          </span>
          <span className="text-xs text-text-secondary">
            {expandedSection === "full-report" ? "▼" : "▶"}
          </span>
        </button>

        {expandedSection === "full-report" && (
          <MarkdownRenderer content={textReport} />
        )}
      </div>
    </div>
  );
}
