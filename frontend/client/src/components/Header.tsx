import { Shield } from "lucide-react";

/**
 * Header Component - BlockStat Branding
 *
 * Design: Cyberpunk aesthetic with neon green glow
 * - Monospace font for terminal feel
 * - Glowing logo with neon green color
 * - Minimal, clean layout
 */
export default function Header() {
  return (
    <header className="border-b border-neon-green/20 bg-dark-bg/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container py-4 md:py-6">
        <div className="flex items-center gap-3">
          <div className="p-2 border border-neon-green/50 rounded">
            <Shield className="w-6 h-6 text-neon-green" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-neon-green">
              BLOCKSTAT
            </h1>
            <p className="text-xs text-text-secondary tracking-widest">
              FORENSIC GRAPH AGENT
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
