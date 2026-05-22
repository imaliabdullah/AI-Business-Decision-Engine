from src.ai.llm_client import LLMClient
from src.ai.prompts import (
    UBER_AUTO_ANALYST_PROMPT,
    UBER_DECISION_BRIEF_PROMPT,
    UBER_INSIGHT_SUMMARY_PROMPT,
)
from src.analysis.uber_analyzer import UberDataAnalyzer
from src.models.uber_schemas import UberAnalyticsResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


class InsightGenerator:
    """Coordinates prompt construction and LLM execution for Uber rides intelligence."""

    def __init__(self) -> None:
        self.llm = LLMClient()

    def generate_decision_brief(self, result: UberAnalyticsResult) -> str:
        logger.info("Generating decision brief")
        context = UberDataAnalyzer.build_context_string(result)
        prompt = UBER_DECISION_BRIEF_PROMPT.format(context=context)
        return self.llm.generate(prompt)

    def generate_auto_analyst(self, result: UberAnalyticsResult) -> str:
        logger.info("Generating auto-analyst insights")
        context = UberDataAnalyzer.build_context_string(result)
        prompt = UBER_AUTO_ANALYST_PROMPT.format(context=context)
        return self.llm.generate(prompt)

    def generate_insight_summary(self, result: UberAnalyticsResult) -> str:
        logger.info("Generating insight summary")
        context = UberDataAnalyzer.build_context_string(result)
        prompt = UBER_INSIGHT_SUMMARY_PROMPT.format(context=context)
        return self.llm.generate(prompt)
