import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/common/Layout';
import DashboardPage from './pages/DashboardPage';
import PortfolioPage from './pages/PortfolioPage';
import NewsPage from './pages/NewsPage';
import ChartPage from './pages/ChartPage';
import StockDetailPage from './pages/StockDetailPage';
import StockAnalysisPage from './pages/StockAnalysisPage';
import OpeningAnalysisPage from './pages/OpeningAnalysisPage';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/news" element={<NewsPage />} />
          <Route path="/chart" element={<ChartPage />} />
          <Route path="/stock/:symbol" element={<StockDetailPage />} />
          <Route path="/analysis" element={<StockAnalysisPage />} />
          <Route path="/opening-analysis" element={<OpeningAnalysisPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
