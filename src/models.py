"""Data models for nutrition information."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NutritionInfo(BaseModel):
    """Nutrition information for a food item."""

    food_name: str = Field(..., description="Name of the food or dish")
    calories: float = Field(..., description="Calories in kcal")
    protein_g: float = Field(..., description="Protein in grams")
    carbs_g: float = Field(..., description="Carbohydrates in grams")
    fats_g: float = Field(..., description="Fats in grams")
    fiber_g: float = Field(..., description="Fiber in grams")
    serving_size: str = Field(..., description="Description of serving size")
    confidence: str = Field(..., description="Confidence level: high, medium, or low")

    def format_message(self) -> str:
        """Format nutrition info as a user-friendly message.

        Returns:
            Formatted string for Telegram message
        """
        return f"""🍽️ **{self.food_name}**

📊 **Nutritional Information**
Serving Size: {self.serving_size}

• Calories: {self.calories:.0f} kcal
• Protein: {self.protein_g:.1f}g
• Carbohydrates: {self.carbs_g:.1f}g
• Fats: {self.fats_g:.1f}g
• Fiber: {self.fiber_g:.1f}g

🎯 Confidence: {self.confidence.capitalize()}

⚠️ *Note: These are estimates based on image analysis. Actual values may vary.*
"""


class ErrorResponse(BaseModel):
    """Error response from OpenAI."""

    error: str = Field(..., description="Error message")


class DailySummary(BaseModel):
    """Daily nutrition summary."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    total_calories: float = Field(..., description="Total calories for the day")
    total_protein_g: float = Field(..., description="Total protein in grams")
    total_carbs_g: float = Field(..., description="Total carbs in grams")
    total_fats_g: float = Field(..., description="Total fats in grams")
    total_fiber_g: float = Field(..., description="Total fiber in grams")
    meal_count: int = Field(..., description="Number of meals analyzed")

    def format_message(self) -> str:
        """Format daily summary as a Telegram message.

        Returns:
            Formatted string for Telegram message
        """
        # Parse date for nice formatting
        try:
            date_obj = datetime.strptime(self.date, '%Y-%m-%d')
            date_str = date_obj.strftime('%b %d, %Y')
        except:
            date_str = self.date

        return f"""📅 **Today's Nutrition Summary**
{date_str}

🍽️ Meals Analyzed: {self.meal_count}

📊 **Total Macros:**
• Calories: {self.total_calories:.0f} kcal
• Protein: {self.total_protein_g:.1f}g
• Carbohydrates: {self.total_carbs_g:.1f}g
• Fats: {self.total_fats_g:.1f}g
• Fiber: {self.total_fiber_g:.1f}g

💪 Great tracking! Keep it up!
"""


class WeeklyStats(BaseModel):
    """Weekly nutrition statistics."""

    start_date: str = Field(..., description="Week start date")
    end_date: str = Field(..., description="Week end date")
    total_analyses: int = Field(..., description="Total number of analyses")
    avg_daily_calories: float = Field(..., description="Average daily calories")
    avg_daily_protein: float = Field(..., description="Average daily protein")
    avg_daily_carbs: float = Field(..., description="Average daily carbs")
    avg_daily_fats: float = Field(..., description="Average daily fats")
    most_common_food: Optional[str] = Field(None, description="Most commonly analyzed food")

    def format_message(self) -> str:
        """Format weekly stats as a Telegram message.

        Returns:
            Formatted string for Telegram message
        """
        most_common = f"🍽️ Most Common: {self.most_common_food}\n" if self.most_common_food else ""

        return f"""📊 **This Week's Statistics**
{self.start_date} to {self.end_date}

📈 **Daily Averages:**
• Calories: {self.avg_daily_calories:.0f} kcal/day
• Protein: {self.avg_daily_protein:.1f}g/day
• Carbs: {self.avg_daily_carbs:.1f}g/day
• Fats: {self.avg_daily_fats:.1f}g/day

{most_common}🔢 Total Meals Tracked: {self.total_analyses}

Keep up the great work! 🎉
"""
