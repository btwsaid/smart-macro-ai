"""OpenAI API client for food image analysis."""

import base64
import json
import logging
from typing import Union
from pathlib import Path

from openai import AsyncOpenAI
from pydantic import ValidationError

from .config import config
from .models import NutritionInfo, ErrorResponse
from .prompts import NUTRITION_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=config.openai_api_key)
        self.model = config.openai_model

    async def analyze_food_image(
        self, image_data: bytes
    ) -> Union[NutritionInfo, ErrorResponse]:
        """Analyze a food image and return nutrition information.

        Args:
            image_data: Image file as bytes

        Returns:
            NutritionInfo object with nutrition data or ErrorResponse on error

        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode("utf-8")

            logger.info(f"Analyzing image with {self.model}")

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": NUTRITION_ANALYSIS_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=config.max_tokens,
                temperature=0.2,  # Lower temperature for more consistent results
            )

            # Extract response content
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content}")

            # Parse JSON response
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {content}")
                return ErrorResponse(
                    error="Failed to parse nutrition data. Please try again."
                )

            # Check if response is an error
            if "error" in data:
                logger.warning(f"OpenAI returned error: {data['error']}")
                return ErrorResponse(error=data["error"])

            # Validate and return nutrition info
            try:
                nutrition_info = NutritionInfo(**data)
                logger.info(
                    f"Successfully analyzed: {nutrition_info.food_name} "
                    f"({nutrition_info.calories} kcal)"
                )
                return nutrition_info
            except ValidationError as e:
                logger.error(f"Validation error: {e}")
                return ErrorResponse(
                    error="Invalid nutrition data format. Please try again."
                )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            return ErrorResponse(
                error=f"Failed to analyze image: {str(e)}"
            )


# Global client instance
openai_client = OpenAIClient()
