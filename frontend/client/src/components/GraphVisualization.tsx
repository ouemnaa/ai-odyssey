import { useEffect, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { AlertTriangle } from "lucide-react";
import type { AnalysisData, Node, Link } from "@/lib/mockData";

interface GraphVisualizationProps {
  data: AnalysisData;
  highlightedWallet: string | null;
  onWalletSelect: (walletId: string | null) => void;
  onNodeClick?: (node: Node) => void;
}

/**
 * GraphVisualization Component - Force-Directed Graph
 *
 * Design: Cyberpunk graph with neon node colors
 * - Red nodes for suspicious wallets
 * - Green nodes for normal wallets
 * - Yellow nodes for deployer
 * - Edge thickness based on transaction volume
 * - Interactive zoom, pan, and node selection
 */
export default function GraphVisualization({
  data,
  highlightedWallet,
  onWalletSelect,
  onNodeClick,
}: GraphVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Update dimensions on mount and resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  // Get node color based on group and highlight state
  const getNodeColor = (node: Node): string => {
    if (highlightedWallet === node.id) {
      return "#ffff00"; // Yellow highlight
    }

    switch (node.group) {
      case "suspicious":
        return "#ff0055"; // Neon pink for suspicious
      case "deployer":
        return "#ffaa00"; // Orange for deployer
      case "mixer":
        return "#ff6600"; // Orange-red for mixer
      case "normal":
      default:
        return "#00ff41"; // Neon green for normal
    }
  };

  // Get node size based on holdings
  const getNodeSize = (node: Node): number => {
    const minSize = 4;
    const maxSize = 20;
    const maxHoldings = Math.max(...data.nodes.map(n => n.value));
    return minSize + (node.value / maxHoldings) * (maxSize - minSize);
  };

  // Get link width based on transaction volume
  const getLinkWidth = (link: Link): number => {
    const maxValue = Math.max(...data.links.map(l => l.value));
    return 0.5 + (link.value / maxValue) * 3;
  };

  // Get link color based on type
  const getLinkColor = (link: Link): string => {
    switch (link.type) {
      case "wash":
        return "rgba(255, 0, 85, 0.3)"; // Pink for wash trading
      case "mixer":
        return "rgba(255, 102, 0, 0.3)"; // Orange for mixer
      case "trade":
        return "rgba(0, 255, 65, 0.2)"; // Green for normal trades
      case "transfer":
      default:
        return "rgba(0, 255, 65, 0.15)"; // Green for transfers
    }
  };

  // Custom node rendering
  const nodeCanvasObject = (node: any, ctx: CanvasRenderingContext2D) => {
    const size = getNodeSize(node);
    const color = getNodeColor(node);

    // Draw node circle
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(node.x || 0, node.y || 0, size, 0, 2 * Math.PI);
    ctx.fill();

    // Draw glow effect for highlighted nodes
    if (highlightedWallet === node.id) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(node.x || 0, node.y || 0, size + 4, 0, 2 * Math.PI);
      ctx.stroke();
    }

    // Draw label for deployer nodes only
    if (node.group === "deployer") {
      ctx.fillStyle = color;
      ctx.font = 'bold 12px "IBM Plex Mono"';
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(node.label.substring(0, 3), node.x || 0, node.y || 0);
    }
  };

  // Custom link rendering
  const linkCanvasObject = (link: any, ctx: CanvasRenderingContext2D) => {
    const width = getLinkWidth(link);
    const color = getLinkColor(link);

    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.moveTo(link.source.x || 0, link.source.y || 0);
    ctx.lineTo(link.target.x || 0, link.target.y || 0);
    ctx.stroke();
  };

  // Handle node click
  const handleNodeClick = (node: Node) => {
    onWalletSelect(highlightedWallet === node.id ? null : node.id);
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  return (
    <div className="neon-card p-0 overflow-hidden h-full min-h-[600px]">
      <div className="flex items-center justify-between p-4 border-b border-neon-green/20">
        <h2 className="text-lg font-bold text-neon-green flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          TRANSACTION GRAPH
        </h2>
        <p className="text-xs text-text-secondary">
          {data.nodes.length} wallets | {data.links.length} transactions
        </p>
      </div>

      <div
        ref={containerRef}
        className="w-full h-full min-h-[500px] bg-dark-bg/50"
      >
        {dimensions.width > 0 && (
          <ForceGraph2D
            ref={graphRef}
            graphData={{
              nodes: data.nodes as any,
              links: data.links as any,
            }}
            width={dimensions.width}
            height={dimensions.height - 60}
            nodeCanvasObject={nodeCanvasObject}
            linkCanvasObject={linkCanvasObject}
            onNodeClick={handleNodeClick}
            nodePointerAreaPaint={(node, color, ctx) => {
              const size = getNodeSize(node as Node);
              ctx.fillStyle = color;
              ctx.beginPath();
              ctx.arc(node.x || 0, node.y || 0, size * 1.5, 0, 2 * Math.PI);
              ctx.fill();
            }}
            d3VelocityDecay={0.3}
            warmupTicks={100}
            cooldownTicks={300}
            backgroundColor="transparent"
          />
        )}
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-neon-green/20 bg-dark-surface/50 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-neon-green"></div>
          <span className="text-text-secondary">Normal Wallet</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-neon-pink"></div>
          <span className="text-text-secondary">Suspicious</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-orange-500"></div>
          <span className="text-text-secondary">Mixer/Deployer</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
          <span className="text-text-secondary">Highlighted</span>
        </div>
      </div>
    </div>
  );
}
