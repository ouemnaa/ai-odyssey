import { Shield } from "lucide-react";
import { useLocation } from "wouter";

/**
 * Header Component - BlockStat Branding
 *
 * Design: Cyberpunk aesthetic with neon green glow
 * - Monospace font for terminal feel
 * - Glowing logo with neon green color
 * - Minimal, clean layout
 * - Navigation tabs for dual-agent system
 */
export default function Header() {
  const [location, setLocation] = useLocation();

  const navItems = [
    { label: "🔬 FORENSIC", path: "/" },
    { label: "🔍 MIXER", path: "/mixer" },
  ];

  return (
    <header className="border-b border-neon-green/20 bg-dark-bg/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container py-4 md:py-6">
        <div className="flex items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 border border-neon-green/50 rounded">
              <Shield className="w-6 h-6 text-neon-green" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-neon-green">
                BLOCKSTAT
              </h1>
              <p className="text-xs text-text-secondary tracking-widest">
                DUAL-AGENT BLOCKCHAIN ANALYSIS
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex gap-4">
          {navItems.map(item => (
            <button
              key={item.path}
              onClick={() => setLocation(item.path)}
              className={`px-4 py-2 text-sm font-bold transition-all duration-200 border-b-2 ${
                location === item.path
                  ? "text-neon-green border-b-neon-green"
                  : "text-text-secondary border-b-transparent hover:text-neon-green hover:border-b-neon-green/50"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
}
