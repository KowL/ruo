import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';

// Global Layout Components
import { Sidebar } from './components/Sidebar';
import { BottomNav } from './components/BottomNav';
import Layout from './components/common/Layout';
import { useSidebarStore } from './store/sidebarStore';
import { PanelLeft } from 'lucide-react';

// New Core Pages
import { HomePage } from './pages/HomePage';
import { AIConsolePage } from './pages/AIConsolePage';
import { LifePage } from './pages/LifePage';
import { SettingsPage } from './pages/SettingsPage';

// Stock Layout & Pages
import { StockLayout } from './pages/stock/StockLayout';
import DashboardPage from './pages/DashboardPage';
import PortfolioPage from './pages/PortfolioPage';
import NewsPage from './pages/NewsPage';
import ChartPage from './pages/ChartPage';
import RadarPage from './pages/RadarPage';
import StrategyPage from './pages/StrategyPage';
import SubscriptionPage from './pages/SubscriptionPage';
import StockAnalysisPage from './pages/StockAnalysisPage';
import OpeningAnalysisPage from './pages/OpeningAnalysisPage';
import ConceptsPage from './pages/concepts/ConceptsPage';
import ConceptDetailPage from './pages/concepts/ConceptDetailPage';
import ConceptMonitorPage from './pages/ConceptMonitorPage';

function AppContent() {
  const { isVisible, toggleSidebar } = useSidebarStore();

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Sidebar Toggle Button - Visible when Sidebar is hidden */}
      {!isVisible && (
        <button
          onClick={toggleSidebar}
          className="fixed left-4 top-4 z-50 p-2 rounded-lg text-[#94A3B8] hover:text-[#F8FAFC] active:bg-[#1E293B] active:border active:border-[#334155] transition-all duration-100 hidden lg:flex"
          title="显示侧边栏"
        >
          <PanelLeft className="w-5 h-5" />
        </button>
      )}

      {/* Sidebar - Desktop Only */}
      <Sidebar />

      {/* Main Content */}
      <main
        className={`${isVisible ? 'lg:ml-[200px]' : 'lg:ml-0'
          } min-h-screen pb-20 lg:pb-0 transition-all duration-300 ease-[0.4, 0, 0.2, 1]`}
      >
        <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
          <AnimatePresence mode="wait">
            <Routes>
              {/* Core App Routes */}
              <Route
                path="/"
                element={
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                  >
                    <HomePage />
                  </motion.div>
                }
              />
              <Route
                path="/ai-console"
                element={
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                  >
                    <AIConsolePage />
                  </motion.div>
                }
              />

              {/* Stock Module with Nested Routing */}
              <Route
                path="/stock"
                element={
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                    className="h-full"
                  >
                    <Layout>
                      <StockLayout />
                    </Layout>
                  </motion.div>
                }
              >
                {/* Default Stock Route is the old Dashboard */}
                <Route index element={<DashboardPage />} />
                <Route path="portfolio" element={<PortfolioPage />} />
                <Route path="subscriptions" element={<SubscriptionPage />} />
                <Route path="news" element={<NewsPage />} />
                <Route path="chart" element={<ChartPage />} />
                <Route path="radar" element={<RadarPage />} />
                <Route path="strategies" element={<StrategyPage />} />
                <Route path="analysis" element={<StockAnalysisPage />} />
                <Route path="opening-analysis" element={<OpeningAnalysisPage />} />
                <Route path="concepts" element={<ConceptsPage />} />
                <Route path="concepts/:id" element={<ConceptDetailPage />} />
                <Route path="concept-monitor" element={<ConceptMonitorPage />} />
              </Route>

              <Route
                path="/life"
                element={
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                  >
                    <LifePage />
                  </motion.div>
                }
              />
              <Route
                path="/settings"
                element={
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                  >
                    <SettingsPage />
                  </motion.div>
                }
              />

              {/* Redirect any unknown route to Home */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AnimatePresence>
        </div>
      </main>

      {/* Bottom Navigation - Mobile Only */}
      <BottomNav />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
