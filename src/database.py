"""Database operations for nutrition history tracking."""

import logging
import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from .config import config
from .models import NutritionInfo

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database manager for nutrition history."""

    def __init__(self):
        """Initialize database with path from config."""
        self.db_path = config.database_path
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        """Initialize database and create tables if they don't exist."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS nutrition_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        username TEXT,
                        food_name TEXT NOT NULL,
                        calories REAL NOT NULL,
                        protein_g REAL NOT NULL,
                        carbs_g REAL NOT NULL,
                        fats_g REAL NOT NULL,
                        fiber_g REAL NOT NULL,
                        serving_size TEXT NOT NULL,
                        confidence TEXT NOT NULL,
                        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        photo_file_id TEXT
                    )
                """)

                # Create indexes for better query performance
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_id
                    ON nutrition_history(user_id)
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analyzed_at
                    ON nutrition_history(analyzed_at)
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_date
                    ON nutrition_history(user_id, analyzed_at)
                """)

                await db.commit()
                logger.info(f"Database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise

    async def save_analysis(
        self,
        user_id: int,
        username: str,
        nutrition_info: NutritionInfo,
        photo_file_id: str
    ) -> bool:
        """Save nutrition analysis to database.

        Args:
            user_id: Telegram user ID
            username: Telegram username or first name
            nutrition_info: NutritionInfo object with analysis results
            photo_file_id: Telegram file ID for the photo

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO nutrition_history (
                        user_id, username, food_name, calories,
                        protein_g, carbs_g, fats_g, fiber_g,
                        serving_size, confidence, photo_file_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    username,
                    nutrition_info.food_name,
                    nutrition_info.calories,
                    nutrition_info.protein_g,
                    nutrition_info.carbs_g,
                    nutrition_info.fats_g,
                    nutrition_info.fiber_g,
                    nutrition_info.serving_size,
                    nutrition_info.confidence,
                    photo_file_id
                ))
                await db.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to save analysis: {e}", exc_info=True)
            return False

    async def get_user_history(
        self,
        user_id: int,
        days: int = 1,
        limit: int = 20
    ) -> List[Dict]:
        """Get user's recent nutrition analyses.

        Args:
            user_id: Telegram user ID
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of nutrition analysis dictionaries
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT * FROM nutrition_history
                    WHERE user_id = ? AND analyzed_at >= ?
                    ORDER BY analyzed_at DESC
                    LIMIT ?
                """, (user_id, cutoff_date, limit)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get user history: {e}", exc_info=True)
            return []

    async def get_daily_summary(self, user_id: int, date: str = None) -> Optional[Dict]:
        """Get nutrition totals for a specific day.

        Args:
            user_id: Telegram user ID
            date: Date string in YYYY-MM-DD format (default: today)

        Returns:
            Dictionary with daily totals or None if no data
        """
        try:
            if date is None:
                date = datetime.utcnow().strftime('%Y-%m-%d')

            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT
                        DATE(analyzed_at) as date,
                        COUNT(*) as meal_count,
                        SUM(calories) as total_calories,
                        SUM(protein_g) as total_protein_g,
                        SUM(carbs_g) as total_carbs_g,
                        SUM(fats_g) as total_fats_g,
                        SUM(fiber_g) as total_fiber_g
                    FROM nutrition_history
                    WHERE user_id = ? AND DATE(analyzed_at) = ?
                    GROUP BY DATE(analyzed_at)
                """, (user_id, date)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None

        except Exception as e:
            logger.error(f"Failed to get daily summary: {e}", exc_info=True)
            return None

    async def get_weekly_stats(self, user_id: int) -> Optional[Dict]:
        """Get statistics for the current week.

        Args:
            user_id: Telegram user ID

        Returns:
            Dictionary with weekly statistics or None if no data
        """
        try:
            # Get start of this week (Monday)
            today = datetime.utcnow()
            start_of_week = today - timedelta(days=today.weekday())
            start_date = start_of_week.strftime('%Y-%m-%d')

            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                # Get aggregated stats
                async with db.execute("""
                    SELECT
                        COUNT(*) as total_analyses,
                        AVG(calories) as avg_calories,
                        AVG(protein_g) as avg_protein,
                        AVG(carbs_g) as avg_carbs,
                        AVG(fats_g) as avg_fats,
                        AVG(fiber_g) as avg_fiber,
                        MIN(DATE(analyzed_at)) as start_date,
                        MAX(DATE(analyzed_at)) as end_date
                    FROM nutrition_history
                    WHERE user_id = ? AND DATE(analyzed_at) >= ?
                """, (user_id, start_date)) as cursor:
                    stats = dict(await cursor.fetchone())

                # Get most common food
                async with db.execute("""
                    SELECT food_name, COUNT(*) as count
                    FROM nutrition_history
                    WHERE user_id = ? AND DATE(analyzed_at) >= ?
                    GROUP BY food_name
                    ORDER BY count DESC
                    LIMIT 1
                """, (user_id, start_date)) as cursor:
                    most_common = await cursor.fetchone()
                    stats['most_common_food'] = dict(most_common)['food_name'] if most_common else None

                return stats if stats['total_analyses'] > 0 else None

        except Exception as e:
            logger.error(f"Failed to get weekly stats: {e}", exc_info=True)
            return None

    async def get_all_time_stats(self, user_id: int) -> Optional[Dict]:
        """Get all-time statistics for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Dictionary with all-time statistics or None if no data
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                # Get overall stats
                async with db.execute("""
                    SELECT
                        COUNT(*) as total_analyses,
                        AVG(calories) as avg_calories,
                        AVG(protein_g) as avg_protein,
                        AVG(carbs_g) as avg_carbs,
                        AVG(fats_g) as avg_fats,
                        MIN(DATE(analyzed_at)) as first_analysis,
                        COUNT(DISTINCT DATE(analyzed_at)) as days_tracked
                    FROM nutrition_history
                    WHERE user_id = ?
                """, (user_id,)) as cursor:
                    stats = dict(await cursor.fetchone())

                # Get top 3 most analyzed foods
                async with db.execute("""
                    SELECT food_name, COUNT(*) as count
                    FROM nutrition_history
                    WHERE user_id = ?
                    GROUP BY food_name
                    ORDER BY count DESC
                    LIMIT 3
                """, (user_id,)) as cursor:
                    top_foods = await cursor.fetchall()
                    stats['top_foods'] = [dict(row) for row in top_foods]

                return stats if stats['total_analyses'] > 0 else None

        except Exception as e:
            logger.error(f"Failed to get all-time stats: {e}", exc_info=True)
            return None


# Global database instance
database = Database()
