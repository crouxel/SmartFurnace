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
                # Create schedules table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schedules
                    (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create schedule_entries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schedule_entries
                    (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        schedule_id INTEGER,
                        cycle_type TEXT,
                        start_temp INTEGER,
                        end_temp INTEGER,
                        duration TEXT,
                        notes TEXT,
                        position INTEGER,
                        FOREIGN KEY (schedule_id) REFERENCES schedules (id)
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
                cursor.execute("SELECT name FROM schedules ORDER BY name")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching schedules: {e}")
            return []

    @classmethod
    def save_schedule(cls, schedule_name, entries):
        """Save a schedule to the database."""
        try:
            conn = sqlite3.connect(cls.DB_NAME)
            cursor = conn.cursor()
            
            # Delete existing schedule if it exists
            cursor.execute("DELETE FROM schedules WHERE name = ?", (schedule_name,))
            
            # Insert new schedule
            cursor.execute("INSERT INTO schedules (name) VALUES (?)", (schedule_name,))
            schedule_id = cursor.lastrowid
            
            # Insert schedule entries
            for entry in entries:
                cursor.execute("""
                    INSERT INTO schedule_entries 
                    (schedule_id, cycle_type, start_temp, end_temp, duration, notes, position) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    schedule_id,
                    entry['CycleType'],
                    entry['StartTemp'],
                    entry['EndTemp'],
                    entry['Duration'],
                    entry['Notes'],
                    entries.index(entry)
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving schedule '{schedule_name}': {str(e)}")
            return False
            
        finally:
            if conn:
                conn.close()

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