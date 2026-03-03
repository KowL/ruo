import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/common/Layout';
import DashboardPage from './pages/DashboardPage';
import PortfolioPage from './pages/PortfolioPage';
import NewsPage from './pages/NewsPage';
import ChartPage from './pages/ChartPage';
import RadarPage from './pages/RadarPage';
import LhbPage from './pages/LhbPage';
import StrategyPage from './pages/StrategyPage';
import BacktestPage from './pages/BacktestPage';

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
          <Route path="/news" element={<NewsPage />} />
          <Route path="/chart" element={<ChartPage />} />
          <Route path="/radar" element={<RadarPage />} />
          <Route path="/lhb" element={<LhbPage />} />
          <Route path="/strategies" element={<StrategyPage />} />
          <Route path="/backtest" element={<BacktestPage />} />

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
