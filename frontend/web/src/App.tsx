import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/common/Layout';
import PortfolioPage from './pages/PortfolioPage';
import NewsPage from './pages/NewsPage';
import ChartPage from './pages/ChartPage';
import './styles/index.css';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<PortfolioPage />} />
          <Route path="/news" element={<NewsPage />} />
          <Route path="/chart" element={<ChartPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
