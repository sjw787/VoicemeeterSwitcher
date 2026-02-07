'use client';

import { useState, useEffect } from 'react';
import ProfileCard from '@/components/ProfileCard';
import StatusBar from '@/components/StatusBar';
import VolumeControl from '@/components/VolumeControl';
import { Profile, Status } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export default function Home() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [switchingProfile, setSwitchingProfile] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      // Add timeout to prevent infinite loading
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

      const [profilesRes, statusRes] = await Promise.all([
        fetch(`${API_URL}/api/profiles`, { signal: controller.signal }),
        fetch(`${API_URL}/api/status`, { signal: controller.signal })
      ]);

      clearTimeout(timeoutId);

      if (!profilesRes.ok || !statusRes.ok) {
        throw new Error('Failed to fetch data');
      }

      const profilesData = await profilesRes.json();
      const statusData = await statusRes.json();

      setProfiles(profilesData.profiles);
      setStatus(statusData);
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);

      if (err instanceof Error && err.name === 'AbortError') {
        setError(`Connection timeout. Make sure API is running on ${API_URL}`);
      } else {
        setError(`Failed to connect to API at ${API_URL}. Make sure the server is running.`);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Fetch data once on mount
    fetchData();
  }, []);

  const loadProfile = async (profileName: string) => {
    // Prevent concurrent profile switches
    if (switchingProfile) {
      console.log('Profile switch already in progress, ignoring click');
      return;
    }

    try {
      setSwitchingProfile(profileName);
      setProfileError(null);
      setError(null);

      console.log('Loading profile:', profileName);
      const response = await fetch(`${API_URL}/api/profile/load`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ profile_name: profileName }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        let errorMessage = errorData.detail || 'Failed to load profile';

        // Provide user-friendly messages for common errors
        if (errorMessage.includes('VBVMR_Login returned -2')) {
          errorMessage = '⚠️ Please wait - previous profile is still loading. Try again in a moment.';
          setProfileError(profileName); // Mark this profile as having an error
        } else if (errorMessage.includes('VBVMR_Login')) {
          errorMessage = '⚠️ Cannot connect to Voicemeeter. Make sure it is running.';
          setProfileError(profileName);
        }

        console.error('API Error:', errorData);
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('Profile loaded successfully:', result);

      // Refresh data immediately
      await fetchData();
      setProfileError(null);
    } catch (err) {
      console.error('Error loading profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to load profile');
      // Clear error after 3 seconds
      setTimeout(() => setError(null), 3000);
    } finally {
      setSwitchingProfile(null);
    }
  };

  const cycleProfile = async () => {
    try {
      const response = await fetch(`${API_URL}/api/profile/cycle`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        let errorMessage = errorData.detail || 'Failed to cycle profile';

        // Provide user-friendly messages for common errors
        if (errorMessage.includes('VBVMR_Login returned -2')) {
          errorMessage = '⚠️ Voicemeeter is not running! Please start Voicemeeter Potato and try again.';
        } else if (errorMessage.includes('VBVMR_Login')) {
          errorMessage = '⚠️ Cannot connect to Voicemeeter. Make sure it is running.';
        }

        throw new Error(errorMessage);
      }

      // Refresh data immediately
      await fetchData();
    } catch (err) {
      console.error('Error cycling profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to cycle profile');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-white text-xl mb-4">Connecting to API...</div>
          <div className="text-gray-400 text-sm mb-4">{API_URL}</div>
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto px-3 md:px-4 py-4 md:py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-4 md:mb-8">
            <h1 className="text-2xl md:text-4xl font-bold text-white mb-1 md:mb-2">
              🎚️ Voicemeeter Control
            </h1>
            <p className="text-sm md:text-base text-gray-400">
              Manage your audio profiles with ease
            </p>
          </div>

          {/* Status Bar */}
          {status && <StatusBar status={status} />}

          {/* Volume Control */}
          <VolumeControl apiUrl={API_URL} />

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 md:px-6 py-4 md:py-6 rounded-lg mb-6">
              <div className="flex items-start gap-3">
                <span className="text-2xl">⚠️</span>
                <div className="flex-1">
                  <h3 className="font-bold text-lg mb-2">Connection Error</h3>
                  <p className="mb-3">{error}</p>
                  <div className="text-sm text-red-300 mb-4">
                    <p className="font-semibold mb-1">Troubleshooting:</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Make sure the API server is running (run_api.bat)</li>
                      <li>Check that the API is on port 8080</li>
                      <li>Verify Voicemeeter Potato is running</li>
                    </ul>
                  </div>
                  <button
                    onClick={() => {
                      setLoading(true);
                      setError(null);
                      fetchData();
                    }}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                  >
                    🔄 Retry Connection
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Quick Cycle Button */}
          <div className="mb-6 md:mb-8 flex justify-center">
            <button
              onClick={cycleProfile}
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold py-2.5 md:py-3 px-6 md:px-8 rounded-lg text-sm md:text-base transition-all transform hover:scale-105 shadow-lg touch-manipulation"
            >
              ⏭️ Cycle to Next Profile
            </button>
          </div>

          {/* Profiles Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-6">
            {profiles.map((profile) => (
              <ProfileCard
                key={profile.filename}
                profile={profile}
                isActive={status?.current_profile === profile.filename}
                isLoading={switchingProfile === profile.filename}
                hasError={profileError === profile.filename}
                onLoad={() => loadProfile(profile.filename)}
              />
            ))}
          </div>

          {/* Footer */}
          <div className="mt-12 text-center text-gray-500 text-sm">
            <p>Connected to {API_URL}</p>
            <p className="mt-2">
              Auto-refresh every 2 seconds • {profiles.length} profile(s) available
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
