import abc
from typing import Any, Dict


class BaseResearchAgent(abc.ABC):
    """
    Abstract Base Class for Multi-Agent Research System agents.
    Subclasses implement specialized domain intelligence:
    - FundamentalAnalysisAgent
    - TechnicalAnalysisAgent
    - NewsSentimentAgent (Module 5)
    - RiskAssessmentAgent (Module 6)
    """

    @property
    @abc.abstractmethod
    def agent_name(self) -> str:
        """Unique identifier for the agent."""
        pass

    @abc.abstractmethod
    async def analyze(self, ticker: str, market: str, period: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent analysis logic."""
        pass

