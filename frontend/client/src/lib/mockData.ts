// Mock data for BlockStat Forensic Graph Agent
// This data simulates a token with suspicious activity including:
// - Wash trading patterns
// - Mixer connections
// - Suspicious wallet clusters
// - High wealth concentration (Gini coefficient)

export interface Node {
  id: string;
  label: string;
  group: 'suspicious' | 'normal' | 'deployer' | 'mixer';
  value: number; // Holdings in tokens
  transactions: number;
  riskScore?: number;
  description?: string;
}

export interface Link {
  source: string;
  target: string;
  value: number; // Transaction volume
  type: 'transfer' | 'trade' | 'wash' | 'mixer';
  count: number; // Number of transactions
}

export interface AnalysisData {
  nodes: Node[];
  links: Link[];
  riskScore: number;
  metrics: {
    giniCoefficient: number;
    washTradingScore: number;
    mixerConnectionsCount: number;
    suspiciousClustersDetected: number;
  };
  topInfluentialWallets: Array<{
    address: string;
    pageRankScore: number;
    holdings: number;
    riskLevel: 'critical' | 'high' | 'medium' | 'low';
  }>;
  detectedCommunities: Array<{
    id: string;
    name: string;
    walletCount: number;
    suspicionLevel: 'critical' | 'high' | 'medium';
    description: string;
  }>;
  redFlags: Array<{
    id: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    title: string;
    description: string;
    affectedWallets: string[];
  }>;
}

// Sample token addresses for the UI
export const SAMPLE_TOKENS = [
  { address: '0x1234567890123456789012345678901234567890', name: 'Suspicious Token (Demo)' },
  { address: '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd', name: 'Risky Token (Demo)' },
  { address: '0x9876543210987654321098765432109876543210', name: 'Wash Trading Token (Demo)' },
];

// Generate mock graph data
export function generateMockData(tokenAddress: string): AnalysisData {
  // Deployer wallet
  const deployerWallet = 'wallet_deployer_001';
  
  // Suspicious wallets (wash trading ring)
  const suspiciousWallets = Array.from({ length: 10 }, (_, i) => 
    `wallet_suspicious_${String(i + 1).padStart(2, '0')}`
  );

  // Mixer wallets (connected to privacy mixers)
  const mixerWallets = Array.from({ length: 5 }, (_, i) => 
    `wallet_mixer_${String(i + 1).padStart(2, '0')}`
  );

  // Normal wallets - generate remaining to reach 50 total
  const normalWalletCount = 50 - 1 - suspiciousWallets.length - mixerWallets.length;
  const normalWallets = Array.from({ length: normalWalletCount }, (_, i) => 
    `wallet_normal_${String(i + 1).padStart(2, '0')}`
  );

  // Create nodes
  const nodes: Node[] = [
    {
      id: deployerWallet,
      label: 'Deployer',
      group: 'deployer',
      value: 5000000,
      transactions: 150,
      riskScore: 45,
      description: 'Token deployer - initial liquidity provider',
    },
    ...suspiciousWallets.map((id, idx) => ({
      id,
      label: `Suspicious Wallet ${idx + 1}`,
      group: 'suspicious' as const,
      value: 250000 + Math.random() * 500000,
      transactions: 45 + Math.random() * 60,
      riskScore: 78 + Math.random() * 20,
      description: 'Part of suspected wash trading ring',
    })),
    ...mixerWallets.map((id, idx) => ({
      id,
      label: `Mixer Connection ${idx + 1}`,
      group: 'mixer' as const,
      value: 150000 + Math.random() * 300000,
      transactions: 25 + Math.random() * 40,
      riskScore: 65 + Math.random() * 25,
      description: 'Connected to privacy mixer service',
    })),
    ...normalWallets.map((id, idx) => ({
      id,
      label: `Wallet ${idx + 1}`,
      group: 'normal' as const,
      value: 50000 + Math.random() * 200000,
      transactions: 10 + Math.random() * 30,
      riskScore: 15 + Math.random() * 20,
      description: 'Regular user wallet',
    })),
  ];

  // Create links
  const links: Link[] = [];

  // Deployer to suspicious wallets (initial distribution)
  suspiciousWallets.forEach((wallet) => {
    links.push({
      source: deployerWallet,
      target: wallet,
      value: 100000 + Math.random() * 200000,
      type: 'transfer',
      count: 2,
    });
  });

  // Wash trading pattern: circular transactions between suspicious wallets (in clusters)
  for (let i = 0; i < suspiciousWallets.length; i++) {
    const nextIdx = (i + 1) % suspiciousWallets.length;
    links.push({
      source: suspiciousWallets[i],
      target: suspiciousWallets[nextIdx],
      value: 150000 + Math.random() * 250000,
      type: 'wash',
      count: 8 + Math.floor(Math.random() * 12),
    });
  }

  // Suspicious wallets to mixer (sample to avoid too many links)
  suspiciousWallets.slice(0, Math.min(50, suspiciousWallets.length)).forEach((wallet) => {
    const randomMixer = mixerWallets[Math.floor(Math.random() * mixerWallets.length)];
    links.push({
      source: wallet,
      target: randomMixer,
      value: 100000 + Math.random() * 150000,
      type: 'mixer',
      count: 3 + Math.floor(Math.random() * 4),
    });
  });

  // Mixer to normal wallets (sampling for performance)
  const sampleMixers = mixerWallets.slice(0, Math.min(20, mixerWallets.length));
  const sampleNormalWallets = normalWallets.slice(0, Math.min(500, normalWallets.length));
  
  sampleMixers.forEach((mixer) => {
    sampleNormalWallets.forEach((wallet) => {
      if (Math.random() > 0.7) {
        links.push({
          source: mixer,
          target: wallet,
          value: 50000 + Math.random() * 100000,
          type: 'transfer',
          count: 2 + Math.floor(Math.random() * 3),
        });
      }
    });
  });

  // Normal wallet interactions (sparse to maintain performance)
  for (let i = 0; i < Math.min(5000, normalWallets.length); i++) {
    if (Math.random() > 0.8) {
      const randomNormal1 = normalWallets[Math.floor(Math.random() * normalWallets.length)];
      const randomNormal2 = normalWallets[Math.floor(Math.random() * normalWallets.length)];
      if (randomNormal1 !== randomNormal2) {
        links.push({
          source: randomNormal1,
          target: randomNormal2,
          value: 30000 + Math.random() * 80000,
          type: 'trade',
          count: 1 + Math.floor(Math.random() * 3),
        });
      }
    }
  }

  // Calculate metrics
  const totalHoldings = nodes.reduce((sum, node) => sum + node.value, 0);
  const sortedHoldings = nodes.map((n) => n.value).sort((a, b) => b - a);
  
  // Gini coefficient calculation (simplified)
  let giniSum = 0;
  for (let i = 0; i < sortedHoldings.length; i++) {
    giniSum += (i + 1) * sortedHoldings[i];
  }
  const giniCoefficient = (2 * giniSum) / (sortedHoldings.length * totalHoldings) - (sortedHoldings.length + 1) / sortedHoldings.length;

  return {
    nodes,
    links,
    riskScore: 78,
    metrics: {
      giniCoefficient: Math.min(giniCoefficient, 0.95),
      washTradingScore: 82,
      mixerConnectionsCount: mixerWallets.length,
      suspiciousClustersDetected: Math.ceil(suspiciousWallets.length / 50),
    },
    topInfluentialWallets: [
      {
        address: deployerWallet,
        pageRankScore: 0.28,
        holdings: 5000000,
        riskLevel: 'high',
      },
      {
        address: suspiciousWallets[0],
        pageRankScore: 0.24,
        holdings: 450000,
        riskLevel: 'critical',
      },
      {
        address: suspiciousWallets[1],
        pageRankScore: 0.22,
        holdings: 420000,
        riskLevel: 'critical',
      },
      {
        address: mixerWallets[0],
        pageRankScore: 0.15,
        holdings: 380000,
        riskLevel: 'high',
      },
      {
        address: normalWallets[0],
        pageRankScore: 0.11,
        holdings: 180000,
        riskLevel: 'low',
      },
    ],
    detectedCommunities: [
      {
        id: 'community_1',
        name: 'Wash Trading Ring',
        walletCount: suspiciousWallets.length,
        suspicionLevel: 'critical',
        description: `Circular transaction pattern detected between ${suspiciousWallets.length} wallets with high frequency and similar volumes. Consistent with coordinated wash trading activity.`,
      },
      {
        id: 'community_2',
        name: 'Mixer-Connected Cluster',
        walletCount: mixerWallets.length + Math.min(500, normalWallets.length),
        suspicionLevel: 'high',
        description: 'Group of wallets with connections to known privacy mixers. Pattern suggests attempt to obscure transaction origins.',
      },
    ],
    redFlags: [
      {
        id: 'flag_1',
        severity: 'critical',
        title: 'Circular Transaction Pattern',
        description: `Detected circular transactions between ${suspiciousWallets.length} wallets with high frequency. This pattern is characteristic of wash trading where the same tokens are repeatedly traded between coordinated accounts to artificially inflate trading volume.`,
        affectedWallets: suspiciousWallets,
      },
      {
        id: 'flag_2',
        severity: 'critical',
        title: 'High Gini Coefficient (0.89)',
        description: 'Wealth is heavily concentrated in a small number of wallets. The deployer and suspicious wallets control a significant portion of the token supply, indicating potential for price manipulation.',
        affectedWallets: [deployerWallet, ...suspiciousWallets.slice(0, 10)],
      },
      {
        id: 'flag_3',
        severity: 'high',
        title: 'Mixer Connections Detected',
        description: 'Multiple wallets have direct connections to known privacy mixer services. This behavior is often used to obscure the source of funds and hide illicit activity.',
        affectedWallets: mixerWallets,
      },
      {
        id: 'flag_4',
        severity: 'high',
        title: 'Rapid Token Distribution',
        description: `Large quantities of tokens distributed to ${suspiciousWallets.length} wallets within a short timeframe, followed by coordinated trading activity. Pattern suggests orchestrated market manipulation.`,
        affectedWallets: suspiciousWallets,
      },
      {
        id: 'flag_5',
        severity: 'medium',
        title: 'Unusual Transaction Frequency',
        description: 'Several wallets show abnormally high transaction frequency compared to normal user behavior, suggesting automated or coordinated trading.',
        affectedWallets: suspiciousWallets.slice(0, 20),
      },
    ],
  };
}

// Export a default dataset for initial load
export const DEFAULT_ANALYSIS = generateMockData('0x1234567890123456789012345678901234567890');
