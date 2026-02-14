"""Main Telegram bot logic."""

import asyncio
import logging
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode, ChatAction

from .config import config
from .openai_client import openai_client
from .models import NutritionInfo, ErrorResponse, DailySummary, WeeklyStats
from .database import database

logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=config.telegram_bot_token)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command.

    Args:
        message: Telegram message object
    """
    welcome_text = """👋 Welcome to **SmartMacro AI Bot**!

🍽️ I analyze food images and provide detailed nutritional information.

**How to use:**
1. Send me a photo of your food
2. I'll analyze it and return nutritional macros
3. Get instant nutrition info in ~2 seconds!

**What I provide:**
• Calories
• Protein, Carbs, Fats
• Fiber content
• Serving size estimation

**Track Your Progress:**
• /history [days] - View recent meals
• /today - Today's nutrition summary
• /week - This week's stats
• /stats - All-time statistics

Just send a photo to get started! 📸
"""
    await message.answer(welcome_text, parse_mode=ParseMode.MARKDOWN)
    logger.info(f"User {message.from_user.id} started the bot")


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command.

    Args:
        message: Telegram message object
    """
    help_text = """📖 **How to Use SmartMacro AI Bot**

**Basic Usage:**
• Send a photo of your food
• Wait for AI analysis (~2 seconds)
• Receive detailed nutrition information

**Tips for Best Results:**
✅ Take clear, well-lit photos
✅ Show the entire portion
✅ Capture food from a top-down angle
❌ Avoid blurry or dark images

**Commands:**
/start - Start the bot
/help - Show this help message
/history [days] - View recent meals (default: today)
/today - Today's nutrition summary
/week - This week's statistics
/stats - All-time statistics

**Note:** Nutritional values are estimates based on visual analysis. Actual values may vary.

Need support? Have questions? Just send me a food photo and let's get started! 🚀
"""
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)
    logger.info(f"User {message.from_user.id} requested help")


@dp.message(F.photo)
async def handle_photo(message: Message) -> None:
    """Handle photo messages and analyze food.

    Args:
        message: Telegram message object with photo
    """
    user_id = message.from_user.id
    logger.info(f"Received photo from user {user_id}")

    try:
        # Send typing action to show bot is processing
        await bot.send_chat_action(
            chat_id=message.chat.id, action=ChatAction.TYPING
        )

        # Get the largest photo (best quality)
        photo = message.photo[-1]

        # Download photo
        photo_file = await bot.get_file(photo.file_id)
        photo_bytes = BytesIO()
        await bot.download_file(photo_file.file_path, photo_bytes)
        image_data = photo_bytes.getvalue()

        logger.info(f"Downloaded photo: {len(image_data)} bytes")

        # Analyze image with OpenAI
        result = await openai_client.analyze_food_image(image_data)

        # Handle response
        if isinstance(result, NutritionInfo):
            # Success - send formatted nutrition info
            response_text = result.format_message()
            await message.answer(response_text, parse_mode=ParseMode.MARKDOWN)
            logger.info(
                f"Successfully sent nutrition info for {result.food_name} "
                f"to user {user_id}"
            )

            # Save to database
            try:
                await database.save_analysis(
                    user_id=user_id,
                    username=message.from_user.username or message.from_user.first_name or "Unknown",
                    nutrition_info=result,
                    photo_file_id=photo.file_id
                )
                logger.info(f"Saved analysis to database for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to save to database: {e}", exc_info=True)
                # Don't fail the user request, just log the error
        elif isinstance(result, ErrorResponse):
            # Error from OpenAI or validation
            error_text = f"❌ **Unable to Analyze Image**\n\n{result.error}\n\n💡 Try sending a clearer photo of food."
            await message.answer(error_text, parse_mode=ParseMode.MARKDOWN)
            logger.warning(f"Error analyzing image for user {user_id}: {result.error}")
        else:
            # Unexpected response type
            await message.answer(
                "❌ Unexpected error occurred. Please try again.",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.error(f"Unexpected result type: {type(result)}")

    except Exception as e:
        logger.error(f"Error handling photo from user {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ **Error Processing Image**\n\n"
            "Sorry, something went wrong. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )


@dp.message(Command("history"))
async def cmd_history(message: Message) -> None:
    """Show user's recent nutrition history.

    Args:
        message: Telegram message object
    """
    user_id = message.from_user.id

    # Parse optional days parameter
    try:
        parts = message.text.split()
        days = int(parts[1]) if len(parts) > 1 else 1
        days = max(1, min(days, 30))  # Limit between 1 and 30 days
    except (ValueError, IndexError):
        days = 1

    try:
        history = await database.get_user_history(user_id, days=days)

        if not history:
            await message.answer(
                "📋 **No meal history found**\n\n"
                f"You haven't analyzed any meals in the last {days} day(s).\n\n"
                "📸 Send a food photo to start tracking!",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Format history message
        period = "Today" if days == 1 else f"Last {days} Days"
        response = f"📋 **Your Recent Meals ({period})**\n\n"

        for idx, entry in enumerate(history, 1):
            # Parse timestamp
            try:
                from datetime import datetime
                analyzed_at = datetime.fromisoformat(entry['analyzed_at'])
                time_str = analyzed_at.strftime('%I:%M %p')
            except:
                time_str = "Unknown time"

            response += f"{idx}. 🍽️ **{entry['food_name']}**\n"
            response += f"   • {entry['calories']:.0f} kcal | "
            response += f"P: {entry['protein_g']:.0f}g C: {entry['carbs_g']:.0f}g F: {entry['fats_g']:.0f}g\n"
            response += f"   • {time_str}\n\n"

        response += "💡 Use /today for daily summary"

        await message.answer(response, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Sent history to user {user_id}")

    except Exception as e:
        logger.error(f"Error getting history for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Unable to load history. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )


@dp.message(Command("today"))
async def cmd_today(message: Message) -> None:
    """Show today's nutrition summary.

    Args:
        message: Telegram message object
    """
    user_id = message.from_user.id

    try:
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        summary_data = await database.get_daily_summary(user_id, today)

        if not summary_data:
            await message.answer(
                "📅 **No meals analyzed today**\n\n"
                "Send a food photo to start tracking your nutrition today!",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Create DailySummary object and format
        summary = DailySummary(**summary_data)
        response = summary.format_message()

        await message.answer(response, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Sent daily summary to user {user_id}")

    except Exception as e:
        logger.error(f"Error getting daily summary for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Unable to load today's summary. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )


@dp.message(Command("week"))
async def cmd_week(message: Message) -> None:
    """Show this week's statistics.

    Args:
        message: Telegram message object
    """
    user_id = message.from_user.id

    try:
        stats_data = await database.get_weekly_stats(user_id)

        if not stats_data:
            await message.answer(
                "📊 **No data for this week**\n\n"
                "Start tracking your meals to see weekly statistics!",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Create WeeklyStats object and format
        stats = WeeklyStats(
            start_date=stats_data['start_date'] or "This week",
            end_date=stats_data['end_date'] or "Today",
            total_analyses=stats_data['total_analyses'],
            avg_daily_calories=stats_data['avg_calories'] or 0,
            avg_daily_protein=stats_data['avg_protein'] or 0,
            avg_daily_carbs=stats_data['avg_carbs'] or 0,
            avg_daily_fats=stats_data['avg_fats'] or 0,
            most_common_food=stats_data.get('most_common_food')
        )
        response = stats.format_message()

        await message.answer(response, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Sent weekly stats to user {user_id}")

    except Exception as e:
        logger.error(f"Error getting weekly stats for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Unable to load weekly statistics. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )


@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Show all-time statistics.

    Args:
        message: Telegram message object
    """
    user_id = message.from_user.id

    try:
        stats_data = await database.get_all_time_stats(user_id)

        if not stats_data:
            await message.answer(
                "📊 **No statistics yet**\n\n"
                "Start analyzing meals to build your nutrition history!",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Format all-time stats
        response = "📊 **All-Time Statistics**\n\n"
        response += f"🔢 Total Analyses: {stats_data['total_analyses']}\n"
        response += f"📅 Tracking Since: {stats_data['first_analysis']}\n"
        response += f"📆 Days Tracked: {stats_data['days_tracked']}\n\n"

        response += "📈 **Average Daily Nutrition:**\n"
        response += f"• Calories: {stats_data['avg_calories']:.0f} kcal/day\n"
        response += f"• Protein: {stats_data['avg_protein']:.1f}g/day\n"
        response += f"• Carbs: {stats_data['avg_carbs']:.1f}g/day\n"
        response += f"• Fats: {stats_data['avg_fats']:.1f}g/day\n\n"

        if stats_data.get('top_foods'):
            response += "🏆 **Most Analyzed Foods:**\n"
            for idx, food in enumerate(stats_data['top_foods'], 1):
                response += f"{idx}. {food['food_name']} ({food['count']}x)\n"
            response += "\n"

        response += f"💪 You've been tracking for {stats_data['days_tracked']} days!"

        await message.answer(response, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Sent all-time stats to user {user_id}")

    except Exception as e:
        logger.error(f"Error getting all-time stats for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Unable to load statistics. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )


@dp.message()
async def handle_other(message: Message) -> None:
    """Handle all other messages.

    Args:
        message: Telegram message object
    """
    await message.answer(
        "🤔 I only understand photos of food!\n\n"
        "📸 Send me a picture of your meal to get nutritional information.\n\n"
        "Use /help for more information.",
        parse_mode=ParseMode.MARKDOWN
    )


async def main() -> None:
    """Main function to start the bot."""
    logger.info("Starting SmartMacro AI Bot...")
    logger.info(f"Using OpenAI model: {config.openai_model}")

    # Initialize database
    try:
        await database.init()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        logger.warning("Bot will continue without database functionality")

    try:
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
