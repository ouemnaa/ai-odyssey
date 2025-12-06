/**
 * Analysis Service - Frontend API Integration
 * Handles all communication with the backend forensics API
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface AnalysisRequest {
  tokenAddress: string;
  daysBack?: number;
  sampleSize?: number;
}

export interface AnalysisResponse {
  analysisId: string;
  status: string;
  timestamp: string;
}

export interface StatusResponse {
  status: 'queued' | 'fetching_data' | 'building_graph' | 'detecting_patterns' | 'completed' | 'failed';
  progress: number;
  currentStep: string;
  errorMessage?: string;
}

export interface Node {
  id: string;
  label: string;
  group: 'suspicious' | 'normal' | 'deployer' | 'mixer';
  value: number;
  transactions: number;
  riskScore?: number;
}

export interface Link {
  source: string;
  target: string;
  value: number;
  type: 'transfer' | 'trade' | 'wash' | 'mixer';
  count: number;
}

export interface TopInfluentialWallet {
  address: string;
  pageRankScore: number;
  holdings: number;
  riskLevel: 'critical' | 'high' | 'medium' | 'low';
}

export interface DetectedCommunity {
  id: string;
  name: string;
  walletCount: number;
  suspicionLevel: 'critical' | 'high' | 'medium';
  description: string;
}

export interface RedFlag {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  affectedWallets?: string[];
}

export interface RiskMetrics {
  giniCoefficient: number;
  washTradingScore: number;
  mixerConnectionsCount: number;
  suspiciousClustersDetected: number;
}

export interface AnalysisData {
  nodes: Node[];
  links: Link[];
  riskScore: number;
  metrics: RiskMetrics;
  topInfluentialWallets: TopInfluentialWallet[];
  detectedCommunities: DetectedCommunity[];
  redFlags: RedFlag[];
}

/**
 * Submit a new token for analysis
 */
export async function submitAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tokenAddress: request.tokenAddress,
        daysBack: request.daysBack || 7,
        sampleSize: request.sampleSize || 5000,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const data: AnalysisResponse = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to submit analysis:', error);
    throw error;
  }
}

/**
 * Check the status of an ongoing analysis
 */
export async function checkAnalysisStatus(analysisId: string): Promise<StatusResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}/status`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const data: StatusResponse = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to check status:', error);
    throw error;
  }
}

/**
 * Get the complete analysis results
 */
export async function getAnalysisResults(analysisId: string): Promise<AnalysisData> {
  try {
    const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const data: AnalysisData = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to get analysis results:', error);
    throw error;
  }
}

/**
 * Export analysis results as CSV or JSON
 */
export async function exportAnalysis(analysisId: string, format: 'csv' | 'json'): Promise<Blob> {
  try {
    const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}/export?format=${format}`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const blob = await response.blob();
    return blob;
  } catch (error) {
    console.error('Failed to export analysis:', error);
    throw error;
  }
}

/**
 * List recent analyses
 */
export async function listAnalyses(limit: number = 10, offset: number = 0) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/analyses?limit=${limit}&offset=${offset}`
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to list analyses:', error);
    throw error;
  }
}

/**
 * Health check - verify backend is running
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/api/v1/health`);
    return response.ok;
  } catch {
    return false;
  }
}
