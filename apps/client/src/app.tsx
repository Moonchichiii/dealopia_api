import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '@/';
const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-white font-sans selection:bg-primary-200">
          <Routes>
            <Route path="/" element={
              <main className="flex flex-col items-center justify-center min-h-screen">
                <h1 className="text-6xl font-display font-bold text-primary-600 animate-fade-in">
                  Dealopia
                </h1>
                <p className="mt-4 text-accent-700 animate-slide-up">
                  Eco-friendly local shopping, redefined.
                </p>
              </main>
            } />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}