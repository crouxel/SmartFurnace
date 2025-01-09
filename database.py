import os
import sqlite3
from typing import List, Tuple, Optional
import logging
from contextlib import contextmanager
from version import APP_NAME

# Set up logging to file in AppData
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.getenv('APPDATA'), APP_NAME, 'smartfurnace.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    APP_DATA = os.path.join(os.getenv('APPDATA') or 
                           os.path.expanduser('~/.local/share'),
                           APP_NAME)
    DB_NAME = os.path.join(APP_DATA, 'SmartFurnace.db')
    
    @classmethod
    def initialize_database(cls):
        """Create database directory and file if they don't exist."""
        try:
            logger.info(f"Initializing database at {cls.DB_NAME}")
            os.makedirs(cls.APP_DATA, exist_ok=True)
            
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                # Create schedules table with proper schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schedules
                    (
                        name TEXT PRIMARY KEY,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @classmethod
    @contextmanager
    def get_connection(cls):
        """Context manager for database connections."""
        if not os.path.exists(cls.APP_DATA):
            cls.initialize_database()
            
        conn = None
        try:
            conn = sqlite3.connect(cls.DB_NAME)
            yield conn
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
            logger.info(f"Attempting to save schedule: {name}")
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create table for this schedule
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
                logger.debug(f"Cleared existing data for schedule: {name}")
                
                # Insert new data
                for i, entry in enumerate(data, 1):
                    cursor.execute(f"""
                        INSERT INTO "{name}" 
                        (Cycle, CycleType, StartTemp, EndTemp, CycleTime, Notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (i,) + entry)
                
                # Update schedules table
                cursor.execute("""
                    INSERT OR REPLACE INTO schedules (name) VALUES (?)
                """, (name,))
                
                conn.commit()
                logger.info(f"Schedule '{name}' saved successfully")
                return True
        except Exception as e:
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