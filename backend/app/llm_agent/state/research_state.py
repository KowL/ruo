from typing import TypedDict, List, Dict, Any, Optional

class ResearchState(TypedDict):
    date: str
    raw_limit_ups: List[Dict[str, Any]]
    lhb_data: List[Any]
    f10_data: Dict[str, Any]
    context_notes: List[str]
    next_action: str
    
    # Reports and Analysis
    data_officer_report: Optional[str]
    strategist_thinking: Optional[str]
    risk_controller_alerts: Optional[List[str]]
    day_trading_coach_advice: Optional[List[Any]]
    final_report: Optional[str]
