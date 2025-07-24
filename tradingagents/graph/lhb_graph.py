import os
from langgraph.graph import StateGraph, END
from tradingagents.agents.analysts.lhb_nodes import fetch_lhb_data, analyze_lhb_data, generate_lhb_suggestion, output_lhb_result

class LHBAgentsGraph:
    def __init__(self):
        self.graph = StateGraph()
        self._build_graph()

    def _build_graph(self):
        self.graph.add_node("fetch", fetch_lhb_data)
        self.graph.add_node("analyze", analyze_lhb_data)
        self.graph.add_node("suggest", generate_lhb_suggestion)
        self.graph.add_node("output", output_lhb_result)

        self.graph.add_edge("fetch", "analyze")
        self.graph.add_edge("analyze", "suggest")
        self.graph.add_edge("suggest", "output")

        self.graph.set_entry_point("fetch")
        self.graph.set_finish_point("output")

    def run(self):
        self.graph.run({}) 