import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/common/Layout';
import DashboardPage from './pages/DashboardPage';
import PortfolioPage from './pages/PortfolioPage';
import NewsPage from './pages/NewsPage';
import ChartPage from './pages/ChartPage';
import RadarPage from './pages/RadarPage';
import StrategyPage from './pages/StrategyPage';
import FavoritesPage from './pages/FavoritesPage';
import SubscriptionPage from './pages/SubscriptionPage';

import StockAnalysisPage from './pages/StockAnalysisPage';
import OpeningAnalysisPage from './pages/OpeningAnalysisPage';
import ConceptsPage from './pages/concepts/ConceptsPage';
import ConceptDetailPage from './pages/concepts/ConceptDetailPage';
import ConceptMonitorPage from './pages/ConceptMonitorPage';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
          <Route path="/subscriptions" element={<SubscriptionPage />} />
          <Route path="/news" element={<NewsPage />} />
          <Route path="/chart" element={<ChartPage />} />
          <Route path="/radar" element={<RadarPage />} />
          <Route path="/strategies" element={<StrategyPage />} />

          <Route path="/analysis" element={<StockAnalysisPage />} />
          <Route path="/opening-analysis" element={<OpeningAnalysisPage />} />
          <Route path="/concepts" element={<ConceptsPage />} />
          <Route path="/concepts/:id" element={<ConceptDetailPage />} />
          <Route path="/concept-monitor" element={<ConceptMonitorPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
