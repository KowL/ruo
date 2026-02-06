
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock broken app.models.news module
mock_news = MagicMock()
sys.modules['app.models.news'] = mock_news

from app.services.ai_analysis import AIAnalysisService
from app.models.stock import AnalysisReport

class TestKlineAnalysis(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.ai_analysis.LLMFactory.get_instance') as mock_get_instance:
            self.mock_llm = mock_get_instance.return_value
            self.service = AIAnalysisService(self.mock_db)
            # Ensure safe access
            self.service.llm = self.mock_llm

    @patch('app.services.ai_analysis.get_market_data_service')
    def test_analyze_kline(self, mock_get_md_service):
        # Mock MarketDataService
        mock_md_service = MagicMock()
        mock_get_md_service.return_value = mock_md_service
        
        # Mock K-line fake data
        fake_kline = []
        base_price = 10.0
        for i in range(20):
            fake_kline.append({
                'date': f'2024-01-{i+1:02d}',
                'open': base_price,
                'high': base_price + 0.5,
                'low': base_price - 0.2,
                'close': base_price + 0.3,
                'volume': 10000 + i * 100,
                'changePct': 3.0
            })
            base_price += 0.3
            
        mock_md_service.get_kline_data.return_value = fake_kline
        
        # Mock DB query for existing report
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock LLM response (LangChain AIMessage)
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "summary": "Mock summary",
            "trend": "Mock trend",
            "support_resistance": {
                "support": 10.0,
                "resistance": 20.0,
                "analysis": "Mock analysis"
            },
            "technical_pattern": "Mock pattern",
            "signals": ["Mock signal"],
            "recommendation": "买入",
            "confidence": 0.8,
            "suggestion": "Mock suggestion"
        })
        self.service.llm.invoke.return_value = mock_response
        
        # Run analysis
        symbol = "000001"
        result = self.service.analyze_kline(symbol, days=20)
        
        # Verify result structure
        self.assertIn('trend', result)
        self.assertIn('recommendation', result)
        self.assertIn('support_resistance', result)
        
        print("\nAnalysis Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Verify DB interactions
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        
        # Check values
        self.assertEqual(result['recommendation'], '买入')
        
    def test_analyze_kline_no_data(self):
         with patch('app.services.ai_analysis.get_market_data_service') as mock_get_md:
            mock_md = MagicMock()
            mock_get_md.return_value = mock_md
            mock_md.get_kline_data.return_value = []
            
            with self.assertRaises(ValueError):
                self.service.analyze_kline("000001")

if __name__ == '__main__':
    unittest.main()
