import os
import sqlite3
from typing import List, Tuple, Optional, Dict
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
                        cycle_type TEXT NOT NULL,
                        start_temp INTEGER NOT NULL,
                        end_temp INTEGER NOT NULL,
                        duration TEXT NOT NULL,
                        notes TEXT,
                        position INTEGER,
                        FOREIGN KEY (schedule_id) REFERENCES schedules (id)
                            ON DELETE CASCADE
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False

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
            conn = sqlite3.connect(cls.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching schedules: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @classmethod
    def save_schedule(cls, schedule_name: str, entries: list) -> bool:
        """Save a schedule to the database."""
        try:
            conn = sqlite3.connect(cls.DB_NAME)
            cursor = conn.cursor()
            
            # Drop existing table if it exists
            cursor.execute(f"DROP TABLE IF EXISTS {schedule_name}")
            
            # Create new table
            cursor.execute(f"""
                CREATE TABLE {schedule_name} (
                    Id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Cycle INTEGER NOT NULL,
                    CycleType TEXT NOT NULL,
                    StartTemp INTEGER NOT NULL,
                    EndTemp INTEGER NOT NULL,
                    CycleTime TEXT NOT NULL,
                    Notes TEXT
                )
            """)

            # Insert entries with Cycle number
            for i, entry in enumerate(entries, 1):  # Start counting from 1
                cursor.execute(f"""
                    INSERT INTO {schedule_name} 
                    (Cycle, CycleType, StartTemp, EndTemp, CycleTime, Notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (i,) + entry)

            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving schedule '{schedule_name}': {e}")
            return False
            
        finally:
            if conn:
                conn.close()

    @classmethod
    def delete_schedule(cls, schedule_name: str) -> bool:
        """Delete a schedule from the database."""
        try:
            conn = sqlite3.connect(cls.DB_NAME)
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {schedule_name}")
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting schedule '{schedule_name}': {e}")
            return False
        finally:
            if conn:
                conn.close()

    @classmethod
    def load_schedule(cls, schedule_name: str) -> List[Dict]:
        """Load a schedule from the database."""
        try:
            conn = sqlite3.connect(cls.DB_NAME)
            cursor = conn.cursor()
            
            # Get all entries from the schedule
            cursor.execute(f"""
                SELECT Cycle, CycleType, StartTemp, EndTemp, CycleTime, Notes 
                FROM {schedule_name} 
                ORDER BY Cycle
            """)
            
            entries = []
            for row in cursor.fetchall():
                entries.append({
                    'Cycle': row[0],
                    'CycleType': row[1],
                    'StartTemp': row[2],
                    'EndTemp': row[3],
                    'CycleTime': row[4],
                    'Notes': row[5] if row[5] else ''
                })
            
            return entries
            
        except sqlite3.Error as e:
            logger.error(f"Error loading schedule '{schedule_name}': {e}")
            return None
            
        finally:
            if conn:
                conn.close()