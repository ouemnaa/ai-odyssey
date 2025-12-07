import { useEffect, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { AlertTriangle, Info } from "lucide-react";

interface MixerNode {
  id: string;
  label: string;
  type: "mixer" | "wallet";
  risk_score: number;
  size: number;
  mixer_type?: string;
}

interface MixerLink {
  source: string;
  target: string;
  value?: number;
}

interface MixerGraphData {
  nodes: MixerNode[];
  edges: MixerLink[];
  statistics?: Record<string, any>;
}

interface MixerGraphVisualizationProps {
  data: MixerGraphData;
  onNodeClick?: (node: MixerNode) => void;
}

/**
 * MixerGraphVisualization Component - Force-Directed Graph for Mixer Detection
 *
 * Design: Cyberpunk graph with neon colors
 * - Red/Pink nodes for mixers (high risk)
 * - Cyan nodes for exposed wallets (varying intensity based on risk)
 * - Edge connections show mixer-wallet relationships
 * - Interactive zoom, pan, and node selection
 */
export default function MixerGraphVisualization({
  data,
  onNodeClick,
}: MixerGraphVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedNode, setSelectedNode] = useState<MixerNode | null>(null);

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

  // Get node color based on type and risk score
  const getNodeColor = (node: MixerNode): string => {
    if (selectedNode?.id === node.id) {
      return "#ffff00"; // Yellow highlight for selected
    }

    if (node.type === "mixer") {
      return "#ff0055"; // Neon pink for mixers
    } else {
      // Wallet: gradient from cyan to red based on risk score
      // risk_score ranges from 0 to 1
      const risk = Math.min(Math.max(node.risk_score || 0, 0), 1);

      // Interpolate between cyan (#00ffff) and red (#ff0055)
      if (risk < 0.33) {
        return "#00ffff"; // Cyan for low risk
      } else if (risk < 0.66) {
        return "#ffff00"; // Yellow for medium risk
      } else {
        return "#ff0055"; // Pink for high risk
      }
    }
  };

  // Get node size
  const getNodeSize = (node: MixerNode): number => {
    return node.size || (node.type === "mixer" ? 15 : 10);
  };

  // Handle node click
  const handleNodeClick = (node: any) => {
    const mixerNode: MixerNode = {
      id: node.id,
      label: node.label,
      type: node.type,
      risk_score: node.risk_score,
      size: node.size,
      mixer_type: node.mixer_type,
    };
    setSelectedNode(mixerNode);
    onNodeClick?.(mixerNode);
  };

  // Convert data format for ForceGraph2D
  const graphData = {
    nodes: data.nodes.map(node => ({
      id: node.id,
      label: node.label,
      type: node.type,
      risk_score: node.risk_score,
      size: node.size,
      mixer_type: node.mixer_type,
    })),
    links: data.edges.map(edge => ({
      source: edge.source,
      target: edge.target,
      value: edge.value || 1,
    })),
  };

  return (
    <div className="w-full h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 bg-dark-bg/80 border-b border-neon-green/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-neon-pink" />
            <h3 className="text-lg font-bold text-neon-green">
              MIXER NETWORK GRAPH
            </h3>
          </div>
          <div className="text-xs text-text-secondary">
            {graphData.nodes.length} nodes • {graphData.links.length}{" "}
            connections
          </div>
        </div>
      </div>

      {/* Graph Container */}
      <div
        ref={containerRef}
        className="flex-1 relative bg-gradient-to-b from-dark-bg via-dark-bg/95 to-dark-bg"
        style={{ minHeight: "400px" }}
      >
        {graphData.nodes.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center">
              <AlertTriangle className="w-12 h-12 text-neon-orange mx-auto mb-2 opacity-50" />
              <p className="text-text-secondary">No nodes to display</p>
            </div>
          </div>
        ) : (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            width={dimensions.width}
            height={dimensions.height}
            nodeColor={getNodeColor}
            nodeVal={getNodeSize}
            linkWidth={() => 1}
            linkColor={() => "rgba(0, 255, 255, 0.3)"}
            nodeLabel={(node: any) => `${node.label}\n${node.type}`}
            onNodeClick={handleNodeClick}
            cooldownTime={3000}
            backgroundColor="transparent"
            nodeCanvasObject={(
              node: any,
              ctx: CanvasRenderingContext2D,
              globalScale: number
            ) => {
              const size = getNodeSize(node);
              const color = getNodeColor(node);

              // Draw glow effect
              ctx.fillStyle = color;
              ctx.globalAlpha = 0.2;
              ctx.beginPath();
              ctx.arc(node.x, node.y, size * 2, 0, 2 * Math.PI);
              ctx.fill();

              // Draw node
              ctx.fillStyle = color;
              ctx.globalAlpha = 1;
              ctx.beginPath();
              ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
              ctx.fill();

              // Draw border
              ctx.strokeStyle = color;
              ctx.lineWidth = 0.5;
              ctx.beginPath();
              ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
              ctx.stroke();

              // Draw label if selected
              if (selectedNode?.id === node.id) {
                ctx.fillStyle = "#ffff00";
                ctx.font = `${Math.max(size / 2, 4)}px Arial`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(node.label.substring(0, 6), node.x, node.y);
              }
            }}
            linkCanvasObject={(
              link: any,
              ctx: CanvasRenderingContext2D,
              globalScale: number
            ) => {
              const start = link.source;
              const end = link.target;

              // Draw link
              ctx.strokeStyle = "rgba(0, 255, 255, 0.3)";
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.moveTo(start.x, start.y);
              ctx.lineTo(end.x, end.y);
              ctx.stroke();
            }}
          />
        )}
      </div>

      {/* Footer - Selected Node Info */}
      {selectedNode && (
        <div className="px-4 py-3 bg-dark-bg/80 border-t border-neon-green/30">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-neon-cyan" />
              <span className="text-sm font-bold text-neon-cyan">
                {selectedNode.type === "mixer" ? "MIXER" : "WALLET"}
              </span>
            </div>
            <div className="text-xs text-text-secondary font-mono">
              {selectedNode.id}
            </div>
            {selectedNode.type === "mixer" && selectedNode.mixer_type && (
              <div className="text-xs text-text-secondary">
                Type: {selectedNode.mixer_type}
              </div>
            )}
            {selectedNode.risk_score !== undefined && (
              <div className="text-xs text-text-secondary">
                Risk Score: {(selectedNode.risk_score * 100).toFixed(1)}%
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
