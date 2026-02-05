// src/pages/dashboard/Dashboard.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Store, ChartBar, Package, Users, Settings, CreditCard } from 'lucide-react';
import { useUser } from '@/hooks/useAuth';

const Dashboard = () => {
  const { data: user, isLoading } = useUser();
  const navigate = useNavigate();
  const [userRole, setUserRole] = useState<'customer' | 'shopkeeper'>('customer');

  // Determine role based on user data.
  useEffect(() => {
    if (user?.notification_preferences?.role === 'shopkeeper') {
      setUserRole('shopkeeper');
    } else {
      setUserRole('customer');
    }
  }, [user]);

  // Although ProtectedRoute should handle redirection, we include a safeguard.
  useEffect(() => {
    if (!isLoading && !user) {
      navigate('/signin');
    }
  }, [isLoading, user, navigate]);

  // Define menu items for customer and shopkeeper roles.
  const customerMenuItems = [
    { icon: Package, label: 'My Orders', href: '/dashboard/orders' },
    { icon: Store, label: 'Saved Deals', href: '/dashboard/saved' },
    { icon: Settings, label: 'Settings', href: '/dashboard/settings' },
  ];

  const shopkeeperMenuItems = [
    { icon: Store, label: 'My Store', href: '/dashboard/store' },
    { icon: Package, label: 'Products', href: '/dashboard/products' },
    { icon: ChartBar, label: 'Analytics', href: '/dashboard/analytics' },
    { icon: Users, label: 'Customers', href: '/dashboard/customers' },
    { icon: CreditCard, label: 'Billing', href: '/dashboard/billing' },
    { icon: Settings, label: 'Settings', href: '/dashboard/settings' },
  ];

  const menuItems = userRole === 'shopkeeper' ? shopkeeperMenuItems : customerMenuItems;

  if (isLoading) {
    return (
      <div className="min-h-screen pt-16 flex items-center justify-center">
        <div className="bg-neutral-900/50 backdrop-blur-sm rounded-2xl p-8 border border-neutral-800/50">
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 rounded-full border-4 border-primary-500 border-t-transparent animate-spin mb-4"></div>
            <p className="text-neutral-400">Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  // This safeguard: if no user exists (should not happen), return null.
  if (!user) return null;

  return (
    <div className="min-h-screen pt-16">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 md:col-span-3">
            <div className="bg-neutral-900/50 backdrop-blur-sm rounded-2xl p-6 border border-neutral-800/50">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-12 h-12 rounded-full bg-primary-500/10 flex items-center justify-center">
                  <span className="text-xl font-semibold text-primary-400">
                    {user.email?.[0].toUpperCase()}
                  </span>
                </div>
                <div>
                  <h3 className="font-semibold text-white">{user.email}</h3>
                  <p className="text-sm text-neutral-400 capitalize">{userRole}</p>
                </div>
              </div>

              <nav className="space-y-2">
                {menuItems.map((item) => (
                  <a
                    key={item.href}
                    href={item.href}
                    className="flex items-center space-x-3 px-4 py-3 rounded-xl text-neutral-300 hover:text-white hover:bg-neutral-800/50 transition-colors"
                  >
                    <item.icon size={20} />
                    <span>{item.label}</span>
                  </a>
                ))}
              </nav>
            </div>
          </div>

          <div className="col-span-12 md:col-span-9">
            <div className="bg-neutral-900/50 backdrop-blur-sm rounded-2xl p-6 border border-neutral-800/50">
              <h2 className="text-2xl font-semibold text-white mb-6">
                {userRole === 'shopkeeper' ? 'Store Overview' : 'My Dashboard'}
              </h2>
              {/* Content for each role can be added here */}
              {userRole === 'shopkeeper' ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-neutral-800/50 rounded-xl p-4">
                    <h3 className="text-neutral-400 mb-2">Total Sales</h3>
                    <p className="text-2xl font-semibold text-white">-</p>
                  </div>
                  <div className="bg-neutral-800/50 rounded-xl p-4">
                    <h3 className="text-neutral-400 mb-2">Active Deals</h3>
                    <p className="text-2xl font-semibold text-white">-</p>
                  </div>
                  <div className="bg-neutral-800/50 rounded-xl p-4">
                    <h3 className="text-neutral-400 mb-2">Total Customers</h3>
                    <p className="text-2xl font-semibold text-white">-</p>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-neutral-800/50 rounded-xl p-4">
                    <h3 className="text-neutral-400 mb-2">Active Orders</h3>
                    <p className="text-2xl font-semibold text-white">-</p>
                  </div>
                  <div className="bg-neutral-800/50 rounded-xl p-4">
                    <h3 className="text-neutral-400 mb-2">Saved Deals</h3>
                    <p className="text-2xl font-semibold text-white">-</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
