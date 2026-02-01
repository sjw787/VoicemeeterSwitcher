'use client';

import { useState, useEffect } from 'react';
import ProfileCard from '@/components/ProfileCard';
import StatusBar from '@/components/StatusBar';
import { Profile, Status } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function Home() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [switchingProfile, setSwitchingProfile] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [profilesRes, statusRes] = await Promise.all([
        fetch(`${API_URL}/api/profiles`),
        fetch(`${API_URL}/api/status`)
      ]);

      if (!profilesRes.ok || !statusRes.ok) {
        throw new Error('Failed to fetch data');
      }

      const profilesData = await profilesRes.json();
      const statusData = await statusRes.json();

      setProfiles(profilesData.profiles);
      setStatus(statusData);
      setError(null);
    } catch (err) {
      setError('Failed to connect to Voicemeeter API. Make sure the server is running.');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh every 2 seconds
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
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
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-2">
              🎚️ Voicemeeter Control
            </h1>
            <p className="text-gray-400">
              Manage your audio profiles with ease
            </p>
          </div>

          {/* Status Bar */}
          {status && <StatusBar status={status} />}

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* Quick Cycle Button */}
          <div className="mb-8 flex justify-center">
            <button
              onClick={cycleProfile}
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold py-3 px-8 rounded-lg transition-all transform hover:scale-105 shadow-lg"
            >
              ⏭️ Cycle to Next Profile
            </button>
          </div>

          {/* Profiles Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
