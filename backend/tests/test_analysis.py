from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

@patch("app.api.endpoints.analysis.run_ai_research_analysis")
def test_limit_up_analysis_endpoint(mock_run_analysis):
    # Mock return value
    mock_run_analysis.return_value = {
        "success": True,
        "result": {
            "date": "2023-01-01", 
            "data_officer_report": "Mock Report",
            "strategist_thinking": "Mock Strategy"
        },
        "cached": False,
        "message": "Success"
    }
    
    response = client.post("/api/v1/analysis/limit-up", json={"date": "2023-01-01"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"]["date"] == "2023-01-01"
    
@patch("app.api.endpoints.analysis.run_ai_research_analysis")
def test_limit_up_analysis_endpoint_failure(mock_run_analysis):
    # Mock failure
    mock_run_analysis.return_value = {
        "success": False,
        "error": "Mock Error"
    }
    
    response = client.post("/api/v1/analysis/limit-up", json={})
    
    assert response.status_code == 500
    assert "Mock Error" in response.json()["detail"]
