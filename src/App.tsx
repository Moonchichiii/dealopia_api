import { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ToastContainer } from 'react-toastify';

import { queryClient } from '@/lib/queryClient';
import Layout from '@/components/layout/Layout';
import Loader from '@/components/ui/Loader';
import ProtectedRoute from '@/components/ProtectedRoute';
import { ThemeProvider } from '@/context/ThemeContext';
import 'react-toastify/dist/ReactToastify.css';
import '@/globals.css';

const Home = lazy(() => import('@/pages/Home'));
const SignIn = lazy(() => import('@/components/auth/SignIn'));
const SignUp = lazy(() => import('@/components/auth/SignUp'));
const Dashboard = lazy(() => import('@/pages/dashboard/Dashboard'));
const NotFound = lazy(() => import('@/pages/NotFound'));

function App(): JSX.Element {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <Router>
          <Suspense fallback={<Loader progress={50} />}>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<Home />} />                
                <Route
                  path="signin"
                  element={
                    <ProtectedRoute requireAuth={false}>
                      <SignIn />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="signup"
                  element={
                    <ProtectedRoute requireAuth={false}>
                      <SignUp />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="dashboard/"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route path="*" element={<NotFound />} />
              </Route>
            </Routes>
          </Suspense>
        </Router>
        <ToastContainer position="top-right" autoClose={5000} theme="dark" />
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;