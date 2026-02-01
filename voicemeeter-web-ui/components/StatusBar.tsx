import { Status } from '@/types';

interface StatusBarProps {
  status: Status;
}

export default function StatusBar({ status }: StatusBarProps) {
  return (
    <div className="bg-gray-800/70 backdrop-blur-sm border border-gray-700 rounded-xl p-6 mb-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="text-center md:text-left">
          <div className="text-gray-400 text-sm mb-1">Status</div>
          <div className="flex items-center justify-center md:justify-start gap-2">
            <span className="flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            <span className="text-white font-semibold capitalize">{status.status}</span>
          </div>
        </div>

        <div className="text-center">
          <div className="text-gray-400 text-sm mb-1">Current Profile</div>
          <div className="text-white font-semibold">{status.current_display_name}</div>
        </div>

        <div className="text-center md:text-right">
          <div className="text-gray-400 text-sm mb-1">Profile</div>
          <div className="text-white font-semibold">
            {status.current_index + 1} of {status.total_profiles}
          </div>
        </div>
      </div>
    </div>
  );
}
