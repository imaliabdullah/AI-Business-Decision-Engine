from openai import OpenAI

from src.config.settings import LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Wrapper around the OpenAI LLM provider."""

    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in the environment.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def generate(self, prompt: str) -> str:
        logger.info("Sending prompt to LLM (model=%s)", LLM_MODEL)

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a world-class business analyst.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=LLM_TEMPERATURE,
        )

        content = response.choices[0].message.content
        logger.info("LLM response received (%d chars)", len(content or ""))
        return content or ""
