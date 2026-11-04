
import os
import logging

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_farming_answer(messages):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-5.5").strip()

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. Check your .env file."
        )

    if not messages:
        raise ValueError("Please enter a farming question.")

    try:
        client = OpenAI(api_key=api_key, timeout=30.0)

        instructions = """
        You are AI CropCare, a helpful agricultural assistant.

        Help farmers with:
        - Crop diseases and symptoms
        - Irrigation and water management
        - Soil health
        - Fertilizer guidance
        - Pest management
        - Crop care and farming practices

        Rules:
        - Use simple English.
        - Give clear, practical answers.
        - Ask for crop name and location when needed.
        - Do not pretend to diagnose without sufficient information.
        - Do not invent pesticide or fertilizer doses.
        - Recommend local agricultural experts for serious crop problems.
        - Explain that chemical products must be used according
          to their labels and local agricultural regulations.
        """

        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=messages,
            max_output_tokens=600
        )

        answer = response.output_text

        if not answer:
            raise RuntimeError("The AI returned an empty response.")

        return answer

    except Exception:
        logger.exception("AI CropCare API request failed")
        raise
