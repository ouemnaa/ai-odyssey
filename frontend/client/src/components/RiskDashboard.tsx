import { AlertTriangle, TrendingUp, Zap, Activity } from 'lucide-react';
import type { AnalysisData } from '@/lib/mockData';

interface RiskDashboardProps {
  data: AnalysisData;
  onWalletHighlight: (walletId: string | null) => void;
}

/**
 * RiskDashboard Component - Risk Metrics Panel
 * 
 * Design: Cyberpunk dashboard with color-coded risk levels
 * - Overall risk score with gradient color (green=safe, yellow=caution, red=danger)
 * - Key metrics cards with icons
 * - Top influential wallets list
 */
export default function RiskDashboard({
  data,
  onWalletHighlight,
}: RiskDashboardProps) {
  const getRiskColor = (score: number): string => {
    if (score < 30) return '#00ff41'; // Green - Safe
    if (score < 60) return '#ffaa00'; // Orange - Caution
    return '#ff0055'; // Pink - Danger
  };

  const getRiskLabel = (score: number): string => {
    if (score < 30) return 'SAFE';
    if (score < 60) return 'CAUTION';
    return 'DANGER';
  };

  const riskColor = getRiskColor(data.riskScore);
  const riskLabel = getRiskLabel(data.riskScore);

  const metrics = [
    {
      label: 'GINI COEFFICIENT',
      value: data.metrics.giniCoefficient.toFixed(2),
      icon: TrendingUp,
      description: 'Wealth concentration (0-1)',
      color: data.metrics.giniCoefficient > 0.85 ? '#ff0055' : '#ffaa00',
    },
    {
      label: 'WASH TRADING SCORE',
      value: `${data.metrics.washTradingScore}%`,
      icon: Activity,
      description: 'Suspicious trading patterns',
      color: data.metrics.washTradingScore > 70 ? '#ff0055' : '#ffaa00',
    },
    {
      label: 'MIXER CONNECTIONS',
      value: data.metrics.mixerConnectionsCount,
      icon: Zap,
      description: 'Privacy mixer links detected',
      color: data.metrics.mixerConnectionsCount > 0 ? '#ff0055' : '#00ff41',
    },
    {
      label: 'SUSPICIOUS CLUSTERS',
      value: data.metrics.suspiciousClustersDetected,
      icon: AlertTriangle,
      description: 'Coordinated wallet groups',
      color: data.metrics.suspiciousClustersDetected > 0 ? '#ff0055' : '#00ff41',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Overall Risk Score */}
      <div className="neon-card p-6 text-center">
        <p className="text-xs text-text-secondary mb-3 tracking-widest">OVERALL RISK SCORE</p>
        <div className="relative mb-4">
          <div className="text-5xl font-bold" style={{ color: riskColor }}>
            {data.riskScore}
          </div>
          <div className="text-xs text-text-secondary mt-2 tracking-widest">
            {riskLabel}
          </div>
        </div>

        {/* Risk bar */}
        <div className="w-full h-2 bg-dark-bg rounded overflow-hidden">
          <div
            className="h-full transition-all duration-500"
            style={{
              width: `${data.riskScore}%`,
              backgroundColor: riskColor,
            }}
          ></div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <div key={metric.label} className="neon-card p-3">
              <div className="flex items-start gap-2 mb-2">
                <Icon
                  className="w-4 h-4 flex-shrink-0 mt-0.5"
                  style={{ color: metric.color }}
                />
                <div className="min-w-0">
                  <p className="text-xs font-bold text-neon-green truncate">
                    {metric.label}
                  </p>
                  <p className="text-xs text-text-secondary">
                    {metric.description}
                  </p>
                </div>
              </div>
              <p
                className="text-lg font-bold"
                style={{ color: metric.color }}
              >
                {metric.value}
              </p>
            </div>
          );
        })}
      </div>

      {/* Top Influential Wallets */}
      <div className="neon-card">
        <div className="p-4 border-b border-neon-green/20">
          <h3 className="text-sm font-bold text-neon-green">TOP WALLETS</h3>
        </div>
        <div className="divide-y divide-neon-green/10">
          {data.topInfluentialWallets.map((wallet) => {
            const riskBgColor =
              wallet.riskLevel === 'critical'
                ? 'bg-neon-pink/20'
                : wallet.riskLevel === 'high'
                  ? 'bg-orange-500/20'
                  : 'bg-neon-green/20';

            const riskTextColor =
              wallet.riskLevel === 'critical'
                ? 'text-neon-pink'
                : wallet.riskLevel === 'high'
                  ? 'text-orange-500'
                  : 'text-neon-green';

            return (
              <button
                key={wallet.address}
                onClick={() => onWalletHighlight(wallet.address)}
                className="w-full p-3 text-left hover:bg-dark-bg/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <p className="text-xs font-mono text-text-secondary truncate">
                    {wallet.address.substring(0, 12)}...
                  </p>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${riskBgColor} ${riskTextColor}`}>
                    {wallet.riskLevel.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-text-secondary">
                    PageRank: {wallet.pageRankScore.toFixed(2)}
                  </p>
                  <p className="text-xs text-neon-green font-mono">
                    {(wallet.holdings / 1000).toFixed(0)}K
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
