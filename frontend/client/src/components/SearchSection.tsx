import { useState } from "react";
import { Search, Loader2 } from "lucide-react";

interface SearchSectionProps {
  onAnalyze: (tokenAddress: string) => void;
  isLoading: boolean;
  selectedTokenAddress: string;
  onTokenAddressChange: (address: string) => void;
}

/**
 * SearchSection Component - Token Analysis Input
 *
 * Design: Cyberpunk input with neon glow effects
 * - Large input field for token contract address
 * - Animated ANALYZE button with hover effects
 * - Loading state with spinner
 */
export default function SearchSection({
  onAnalyze,
  isLoading,
  selectedTokenAddress,
  onTokenAddressChange,
}: SearchSectionProps) {
  const [localInput, setLocalInput] = useState(selectedTokenAddress);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAnalyze(localInput);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setLocalInput(value);
    onTokenAddressChange(value);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSubmit(e as any);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-3">
      <div className="relative">
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-neon-green/50">
          <Search className="w-5 h-5" />
        </div>
        <input
          type="text"
          value={localInput}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder="Enter Token Contract Address (e.g., 0x...)"
          className="neon-input w-full pl-12 pr-4 py-3 text-sm md:text-base"
          disabled={isLoading}
        />
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2 text-sm md:text-base px-6 py-2 font-bold bg-neon-green text-dark-bg rounded hover:bg-neon-green/80 transition-colors"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            ANALYZING...
          </>
        ) : (
          <>
            <Search className="w-4 h-4" />
            ANALYZE
          </>
        )}
      </button>
    </form>
  );
}
