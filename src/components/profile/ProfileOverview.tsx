import React from 'react';
import { useUser } from '@/hooks/useAuth';

const ProfileOverview = () => {
  const { data: user, isLoading, error } = useUser();

  if (isLoading) {
    return (
      <div className="p-4 bg-neutral-800 rounded-lg">
        <div className="animate-pulse flex flex-col space-y-4">
          <div className="h-12 bg-neutral-700 rounded"></div>
          <div className="h-8 bg-neutral-700 rounded w-3/4"></div>
          <div className="h-8 bg-neutral-700 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-800/40 rounded-lg text-red-100">
        <h3 className="font-medium mb-2">Error loading profile</h3>
        <p className="text-sm text-red-200">{error?.message || 'User not authenticated'}</p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-neutral-800/50 backdrop-blur-sm rounded-xl border border-neutral-700/50">
      <div className="flex items-center space-x-4 mb-4">
        <div className="bg-primary-500/20 h-12 w-12 rounded-full flex items-center justify-center text-primary-400 font-semibold text-xl">
          {user.first_name ? user.first_name[0].toUpperCase() : user.email[0].toUpperCase()}
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">
            {user.first_name} {user.last_name}
          </h2>
          <p className="text-neutral-400 text-sm">{user.email}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        <div className="bg-neutral-700/30 rounded-lg p-4">
          <h3 className="text-neutral-300 text-sm font-medium mb-2">Account Details</h3>
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between">
              <span className="text-neutral-400">Member since</span>
              <span className="text-white">{user.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'N/A'}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-neutral-400">Last login</span>
              <span className="text-white">{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'N/A'}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-neutral-400">Phone</span>
              <span className="text-white">{user.phone_number || 'Not provided'}</span>
            </li>
          </ul>
        </div>

        <div className="bg-neutral-700/30 rounded-lg p-4">
          <h3 className="text-neutral-300 text-sm font-medium mb-2">Preferences</h3>
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between">
              <span className="text-neutral-400">Language</span>
              <span className="text-white">{user.preferred_language || 'English'}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-neutral-400">2FA Enabled</span>
              <span className="text-white">{user.has_2fa_enabled ? 'Yes' : 'No'}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-neutral-400">Role</span>
              <span className="text-white capitalize">{user.notification_preferences?.role || 'Customer'}</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-neutral-700/50">
        <h3 className="text-neutral-300 text-sm font-medium mb-2">User Stats</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-primary-500/10 rounded-lg p-3 text-center">
            <div className="text-primary-400 text-lg font-semibold">0</div>
            <div className="text-xs text-neutral-400">Favorites</div>
          </div>
          <div className="bg-primary-500/10 rounded-lg p-3 text-center">
            <div className="text-primary-400 text-lg font-semibold">0</div>
            <div className="text-xs text-neutral-400">Redeemed</div>
          </div>
          <div className="bg-primary-500/10 rounded-lg p-3 text-center">
            <div className="text-primary-400 text-lg font-semibold">0</div>
            <div className="text-xs text-neutral-400">Reviews</div>
          </div>
          <div className="bg-primary-500/10 rounded-lg p-3 text-center">
            <div className="text-primary-400 text-lg font-semibold">{user.sustainability_preference || 0}</div>
            <div className="text-xs text-neutral-400">Eco Score</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileOverview;