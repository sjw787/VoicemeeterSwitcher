interface ProfileCardProps {
  profile: {
    filename: string;
    display_name: string;
    index: number;
  };
  isActive: boolean;
  isLoading?: boolean;
  hasError?: boolean;
  onLoad: () => void;
}
export default function ProfileCard({ profile, isActive, isLoading, hasError, onLoad }: ProfileCardProps) {
  const getCardStyle = () => {
    if (isLoading) {
      return "bg-gradient-to-br from-blue-500/30 to-cyan-600/30 border-2 border-blue-500 shadow-xl shadow-blue-500/20 cursor-wait";
    }
    if (hasError) {
      return "bg-gradient-to-br from-yellow-500/30 to-amber-600/30 border-2 border-yellow-500 shadow-xl shadow-yellow-500/20";
    }
    if (isActive) {
      return "bg-gradient-to-br from-green-500/30 to-emerald-600/30 border-2 border-green-500 shadow-xl shadow-green-500/20";
    }
    return "bg-gray-800/50 border-2 border-gray-700 hover:border-gray-600";
  };
  return (
    <div
      className={`relative rounded-xl p-6 transition-all transform hover:scale-105 cursor-pointer ${getCardStyle()}`}
      onClick={isLoading ? undefined : onLoad}
    >
      {isActive && !isLoading && !hasError && (
        <div className="absolute top-3 right-3">
          <span className="flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
        </div>
      )}
      {isLoading && (
        <div className="absolute top-3 right-3">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 rounded-full border-t-transparent"></div>
        </div>
      )}
      {hasError && !isLoading && (
        <div className="absolute top-3 right-3">
          <span className="text-yellow-500 text-xl">⚠️</span>
        </div>
      )}
      <div className="flex items-start justify-between mb-4">
        <div className="text-3xl">🎵</div>
        <div className="text-sm font-mono text-gray-500">#{profile.index + 1}</div>
      </div>
      <h3 className="text-xl font-bold text-white mb-2">{profile.display_name}</h3>
      <p className="text-sm text-gray-400 mb-4 truncate">{profile.filename}</p>
      <button
        onClick={(e) => {
          e.stopPropagation();
          if (!isLoading) onLoad();
        }}
        className={`w-full py-2 px-4 rounded-lg font-semibold transition-colors ${
          isLoading
            ? "bg-blue-600 text-white cursor-wait"
            : hasError
            ? "bg-yellow-600 hover:bg-yellow-700 text-white"
            : isActive
            ? "bg-green-600 text-white cursor-default"
            : "bg-gray-700 hover:bg-gray-600 text-gray-200"
        }`}
        disabled={isActive || isLoading}
      >
        {isLoading ? "⏳ Loading..." : hasError ? "⚠️ Try Again" : isActive ? "✓ Active" : "Load Profile"}
      </button>
    </div>
  );
}
