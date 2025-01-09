import sqlite3
from typing import List, Tuple, Optional
import logging
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    DB_NAME = 'SmartFurnace.db'
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Context manager for database connections to ensure proper closing."""
        conn = None
        try:
            conn = sqlite3.connect(cls.DB_NAME)
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @classmethod
    def fetch_all_schedules(cls) -> List[str]:
        """Fetch all schedule names from the database."""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name != 'sqlite_sequence'
                    ORDER BY name
                """)
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching schedules: {e}")
            return []

    @classmethod
    def save_schedule(cls, name: str, data: List[Tuple]) -> bool:
        """Save or update a schedule in the database."""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create table if it doesn't exist with the correct schema
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS "{name}" (
                        Id INTEGER PRIMARY KEY AUTOINCREMENT,
                        Cycle INTEGER,
                        CycleType TEXT,
                        StartTemp INTEGER,
                        EndTemp INTEGER,
                        CycleTime TEXT,
                        Notes TEXT
                    )
                """)
                
                # Clear existing data
                cursor.execute(f'DELETE FROM "{name}"')
                
                # Insert new data with cycle number
                for i, entry in enumerate(data, 1):
                    cursor.execute(f"""
                        INSERT INTO "{name}" 
                        (Cycle, CycleType, StartTemp, EndTemp, CycleTime, Notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (i,) + entry)
                
                conn.commit()
                logger.info(f"Schedule '{name}' saved successfully")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error saving schedule '{name}': {e}")
            return False

    @classmethod
    def delete_schedule(cls, name: str) -> bool:
        """Delete a schedule from the database."""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'DROP TABLE IF EXISTS "{name}"')
                conn.commit()
                logger.info(f"Schedule '{name}' deleted successfully")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting schedule '{name}': {e}")
            return False

    @classmethod
    def load_schedule(cls, name: str) -> Optional[List[Tuple]]:
        """Load a schedule's data from the database."""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM "{name}"')
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error loading schedule '{name}': {e}")
            return None