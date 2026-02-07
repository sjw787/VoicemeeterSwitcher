'use client';

import { useState, useEffect, useRef } from 'react';
import { VolumeInfo } from '@/types';

interface VolumeControlProps {
  apiUrl: string;
}

export default function VolumeControl({ apiUrl }: VolumeControlProps) {
  const [volume, setVolume] = useState<VolumeInfo | null>(null);
  const [localGain, setLocalGain] = useState<number | null>(null);
  const [isAdjusting, setIsAdjusting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  const fetchVolume = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/volume/a1`);
      if (!response.ok) {
        throw new Error('Failed to fetch volume');
      }
      const data = await response.json();
      setVolume(data);
      if (!isAdjusting) {
        setLocalGain(data.gain);
      }
      setError(null);
    } catch (err) {
      console.error('Error fetching volume:', err);
      setError('Failed to fetch volume');
    }
  };

  useEffect(() => {
    // Fetch volume once on mount
    fetchVolume();
  }, []);

  const sendVolumeToAPI = async (newGain: number) => {
    try {
      const response = await fetch(`${apiUrl}/api/volume/a1`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ gain: newGain }),
      });

      if (!response.ok) {
        throw new Error('Failed to set volume');
      }

      const data = await response.json();
      setVolume(data);
      setError(null);
    } catch (err) {
      console.error('Error setting volume:', err);
      setError('Failed to set volume');
    } finally {
      setIsAdjusting(false);
    }
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newGain = parseFloat(e.target.value);

    // Update UI immediately
    setLocalGain(newGain);
    setIsAdjusting(true);

    // Clear existing timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Set new timer - only send API request after user stops for 500ms
    debounceTimer.current = setTimeout(() => {
      sendVolumeToAPI(newGain);
    }, 500);
  };

  const handleResetClick = () => {
    // Clear any pending debounced updates
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    setLocalGain(0);
    setIsAdjusting(true);
    sendVolumeToAPI(0);
  };

  const formatVolume = (gain: number): string => {
    return `${gain >= 0 ? '+' : ''}${gain.toFixed(1)} dB`;
  };

  const gainToPercent = (gain: number): number => {
    // Map -60 to 12 dB range to 0-100%
    return ((gain + 60) / 72) * 100;
  };

  if (!volume || localGain === null) {
    return null;
  }

  const displayGain = localGain;

  return (
    <div className="bg-gray-800/70 backdrop-blur-sm border border-gray-700 rounded-xl p-4 md:p-6 mb-8">
      {/* Mobile Layout: Stack vertically */}
      <div className="block md:hidden space-y-4">
        {/* Header with volume display */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-gray-400 text-xs mb-1">A1 Output Volume</div>
            <div className="text-white font-bold text-3xl">{formatVolume(displayGain)}</div>
          </div>
          <button
            onClick={handleResetClick}
            className="bg-gray-700 hover:bg-gray-600 active:bg-gray-500 text-white px-4 py-3 rounded-lg transition-colors text-sm font-medium touch-manipulation"
          >
            Reset
          </button>
        </div>

        {/* Large slider for mobile */}
        <div className="py-2">
          <input
            type="range"
            min="-60"
            max="12"
            step="0.5"
            value={displayGain}
            onChange={handleSliderChange}
            className="w-full h-8 bg-gray-700 rounded-lg appearance-none cursor-pointer slider touch-manipulation"
            style={{
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${gainToPercent(displayGain)}%, #374151 ${gainToPercent(displayGain)}%, #374151 100%)`
            }}
          />
          <div className="relative text-sm text-gray-500 mt-3 h-5">
            <span className="absolute left-0">-60 dB</span>
            <span className="absolute" style={{ left: '83.33%', transform: 'translateX(-50%)' }}>0 dB</span>
            <span className="absolute right-0">+12 dB</span>
          </div>
        </div>
      </div>

      {/* Desktop Layout: Horizontal */}
      <div className="hidden md:flex items-center gap-4">
        <div className="flex-shrink-0">
          <div className="text-gray-400 text-sm mb-1">A1 Output Volume</div>
          <div className="text-white font-bold text-2xl">{formatVolume(displayGain)}</div>
        </div>

        <div className="flex-grow">
          <input
            type="range"
            min="-60"
            max="12"
            step="0.5"
            value={displayGain}
            onChange={handleSliderChange}
            className="w-full h-3 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            style={{
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${gainToPercent(displayGain)}%, #374151 ${gainToPercent(displayGain)}%, #374151 100%)`
            }}
          />
          <div className="relative text-xs text-gray-500 mt-1 h-4">
            <span className="absolute left-0">-60 dB</span>
            <span className="absolute" style={{ left: '83.33%', transform: 'translateX(-50%)' }}>0 dB</span>
            <span className="absolute right-0">+12 dB</span>
          </div>
        </div>

        <div className="flex-shrink-0">
          <button
            onClick={handleResetClick}
            className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
          >
            Reset to 0 dB
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-3 text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
