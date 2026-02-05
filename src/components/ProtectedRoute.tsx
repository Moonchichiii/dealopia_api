// src/components/ProtectedRoute.tsx
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useUser } from '@/hooks/useAuth';
import { Loader } from 'lucide-react';

type UserRole = 'SHOPKEEPER' | 'USER';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requiredRoles?: UserRole[]; // Role checking is preserved
}

const ProtectedRoute = ({
  children,
  requireAuth = true,
  requiredRoles,
}: ProtectedRouteProps) => {
  const { data: user, isLoading } = useUser();
  const location = useLocation();

  // While loading, show a full-screen loader.
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-950">
        <div className="bg-neutral-900/50 backdrop-blur-sm rounded-xl p-8 flex flex-col items-center">
          <Loader className="w-6 h-6 text-primary-400 animate-spin" />
          <span className="mt-4 text-neutral-300 font-medium">
            Verifying authentication...
          </span>
        </div>
      </div>
    );
  }

  // If auth is required and no user is present, redirect to signin.
  if (requireAuth && !user) {
    return (
      <Navigate
        to="/signin"
        state={{ from: location.pathname, message: 'Please sign in to access this page' }}
        replace
      />
    );
  }

  // If requiredRoles are specified, check the user's role.
  if (user && requiredRoles && requiredRoles.length > 0) {
    // Here we assume the user's role is stored in notification_preferences.role.
    const userRole = user.notification_preferences?.role || 'USER';
    if (!requiredRoles.includes(userRole)) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-neutral-950">
          <div className="bg-neutral-900/50 backdrop-blur-sm rounded-xl p-8 text-center">
            <span className="text-neutral-300 font-medium">
              You are not authorized to view this page.
            </span>
          </div>
        </div>
      );
    }
  }

  // Redirect away from public pages if the user is already authenticated.
  if (!requireAuth && user) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
