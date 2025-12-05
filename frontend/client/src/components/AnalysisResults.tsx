import { useState } from 'react';
import { ChevronDown, AlertTriangle, Users, Flag } from 'lucide-react';
import type { AnalysisData } from '@/lib/mockData';

interface AnalysisResultsProps {
  data: AnalysisData;
  onWalletHighlight: (walletId: string | null) => void;
}

/**
 * AnalysisResults Component - Detailed Findings
 * 
 * Design: Collapsible panels with cyberpunk styling
 * - Top Influential Wallets (PageRank results)
 * - Detected Communities (wash trading rings)
 * - Red Flags (specific warnings)
 */
export default function AnalysisResults({
  data,
  onWalletHighlight,
}: AnalysisResultsProps) {
  const [expandedSections, setExpandedSections] = useState<{
    [key: string]: boolean;
  }>({
    communities: true,
    redFlags: true,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const getSeverityColor = (
    severity: 'critical' | 'high' | 'medium' | 'low'
  ): string => {
    switch (severity) {
      case 'critical':
        return '#ff0055'; // Pink
      case 'high':
        return '#ffaa00'; // Orange
      case 'medium':
        return '#ffff00'; // Yellow
      case 'low':
        return '#00ff41'; // Green
    }
  };

  const getSuspicionColor = (
    level: 'critical' | 'high' | 'medium'
  ): string => {
    switch (level) {
      case 'critical':
        return '#ff0055';
      case 'high':
        return '#ffaa00';
      case 'medium':
        return '#ffff00';
    }
  };

  return (
    <div className="space-y-4">
      {/* Detected Communities Section */}
      <div className="neon-card overflow-hidden">
        <button
          onClick={() => toggleSection('communities')}
          className="w-full p-4 flex items-center justify-between hover:bg-dark-bg/50 transition-colors border-b border-neon-green/20"
        >
          <div className="flex items-center gap-3">
            <Users className="w-5 h-5 text-neon-green" />
            <h3 className="text-sm font-bold text-neon-green">
              DETECTED COMMUNITIES ({data.detectedCommunities.length})
            </h3>
          </div>
          <ChevronDown
            className={`w-4 h-4 text-neon-green transition-transform ${
              expandedSections.communities ? 'rotate-180' : ''
            }`}
          />
        </button>

        {expandedSections.communities && (
          <div className="divide-y divide-neon-green/10">
            {data.detectedCommunities.map((community) => (
              <div key={community.id} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-bold text-neon-green text-sm">
                    {community.name}
                  </h4>
                  <span
                    className="text-xs font-bold px-2 py-1 rounded"
                    style={{
                      color: getSuspicionColor(community.suspicionLevel),
                      backgroundColor: `${getSuspicionColor(community.suspicionLevel)}20`,
                    }}
                  >
                    {community.suspicionLevel.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-text-secondary mb-2">
                  {community.description}
                </p>
                <p className="text-xs text-text-secondary font-mono">
                  {community.walletCount} wallets in cluster
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Red Flags Section */}
      <div className="neon-card overflow-hidden">
        <button
          onClick={() => toggleSection('redFlags')}
          className="w-full p-4 flex items-center justify-between hover:bg-dark-bg/50 transition-colors border-b border-neon-green/20"
        >
          <div className="flex items-center gap-3">
            <Flag className="w-5 h-5 text-neon-pink" />
            <h3 className="text-sm font-bold text-neon-green">
              RED FLAGS ({data.redFlags.length})
            </h3>
          </div>
          <ChevronDown
            className={`w-4 h-4 text-neon-green transition-transform ${
              expandedSections.redFlags ? 'rotate-180' : ''
            }`}
          />
        </button>

        {expandedSections.redFlags && (
          <div className="divide-y divide-neon-green/10">
            {data.redFlags.map((flag) => (
              <div key={flag.id} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-bold text-sm" style={{ color: getSeverityColor(flag.severity) }}>
                    {flag.title}
                  </h4>
                  <span
                    className="text-xs font-bold px-2 py-1 rounded flex items-center gap-1"
                    style={{
                      color: getSeverityColor(flag.severity),
                      backgroundColor: `${getSeverityColor(flag.severity)}20`,
                    }}
                  >
                    <AlertTriangle className="w-3 h-3" />
                    {flag.severity.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-text-secondary mb-3">
                  {flag.description}
                </p>
                <div className="flex flex-wrap gap-2">
                  {flag.affectedWallets.slice(0, 3).map((wallet) => (
                    <button
                      key={wallet}
                      onClick={() => onWalletHighlight(wallet)}
                      className="text-xs px-2 py-1 bg-dark-bg/50 border border-neon-green/30 text-neon-green hover:border-neon-green transition-colors rounded"
                    >
                      {wallet.substring(0, 10)}...
                    </button>
                  ))}
                  {flag.affectedWallets.length > 3 && (
                    <span className="text-xs text-text-secondary px-2 py-1">
                      +{flag.affectedWallets.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
