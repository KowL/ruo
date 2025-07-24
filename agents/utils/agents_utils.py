from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from typing import List
from typing import Annotated
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import RemoveMessage
from langchain_core.tools import tool
from datetime import date, timedelta, datetime
import functools
import pandas as pd
import os
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
import tradingagents.dataflows.interface as interface
from tradingagents.default_config import DEFAULT_CONFIG
from langchain_core.messages import HumanMessage
import api.stock_api as stock_api

class Toolkit:

    @staticmethod
    @tool
    def get_lhb_data(
        date: Annotated[str, "The date of the data to retrieve"]
    ) -> pd.DataFrame:
        """
        Get the data from the LHB database.
        """
        return stock_api.get_lhb_data(date)