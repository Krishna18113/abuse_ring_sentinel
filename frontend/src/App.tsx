import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';

import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { RiskQueue } from './pages/RiskQueue';
import { Investigation } from './pages/Investigation';
import { MerchantAnalysis } from './pages/MerchantAnalysis';
import { fetchDemoCustomers } from './services/api';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 60 * 1000,
    },
  },
});

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 text-center bg-slate-900/80 border border-slate-800 rounded-xl max-w-lg mx-auto mt-12 space-y-4">
          <h2 className="text-base font-bold text-rose-400">Rendering Exception Encountered</h2>
          <p className="text-xs text-slate-400 font-mono">{this.state.error?.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
          >
            Reload Application
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const AppContent: React.FC = () => {
  const { data: demoCustomers } = useQuery({
    queryKey: ['demo-customers'],
    queryFn: fetchDemoCustomers,
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar demoCustomers={demoCustomers} />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/risk-queue" element={<RiskQueue />} />
            <Route path="/customers/:customerId" element={<Investigation />} />
            <Route path="/merchant-analysis" element={<MerchantAnalysis />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
