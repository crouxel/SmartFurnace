import os
import sqlite3
from typing import List, Tuple, Optional, Dict
import logging
from contextlib import contextmanager
from version import APP_NAME

# Create Windows app data directory
app_data_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), APP_NAME)
os.makedirs(app_data_dir, exist_ok=True)

# Setup logging with error handling
log_file = os.path.join(app_data_dir, 'smartfurnace.log')
try:
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
except Exception as e:
    # Fallback to console logging if file logging fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.warning(f"Failed to create log file: {e}")

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
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM schedules ORDER BY name")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching schedules: {e}", exc_info=True)
            return []

    @classmethod
    def save_schedule(cls, name: str, entries: List[Tuple]) -> bool:
        """Save a schedule to the database.
        
        Args:
            name: Name of the schedule
            entries: List of tuples in format (CycleType, StartTemp, EndTemp, Duration, Notes)
                    DO NOT PASS DICTIONARIES - Must be tuples in exact order above
        Returns:
            bool: True if save successful, False otherwise
        """
        logger.debug(f"Saving schedule '{name}' with {len(entries)} entries")
        
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                
                # First, ensure the schedule exists in schedules table
                cursor.execute("""
                    INSERT OR REPLACE INTO schedules (name, modified_date)
                    VALUES (?, CURRENT_TIMESTAMP)
                """, (name,))
                
                # Get the schedule_id
                cursor.execute("SELECT id FROM schedules WHERE name = ?", (name,))
                schedule_id = cursor.fetchone()[0]
                
                # Clear existing entries for this schedule
                cursor.execute("DELETE FROM schedule_entries WHERE schedule_id = ?", (schedule_id,))
                
                # Insert new entries
                for position, entry in enumerate(entries):
                    cursor.execute("""
                        INSERT INTO schedule_entries 
                        (schedule_id, cycle_type, start_temp, end_temp, duration, notes, position)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (schedule_id, *entry, position))
                
                conn.commit()
                logger.debug(f"Successfully saved schedule '{name}'")
                return True
                
        except Exception as e:
            logger.error(f"Error saving schedule '{name}': {e}", exc_info=True)
            return False

    @classmethod
    def delete_schedule(cls, schedule_name: str) -> bool:
        """Delete a schedule from the database."""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete from schedules table (cascade will handle entries)
                cursor.execute("DELETE FROM schedules WHERE name = ?", (schedule_name,))
                conn.commit()
                
                logger.debug(f"Successfully deleted schedule: {schedule_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting schedule '{schedule_name}': {e}", exc_info=True)
            return False

    @classmethod
    def load_schedule(cls, schedule_name: str) -> List[Dict]:
        """Load a schedule from the database."""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get schedule ID
                cursor.execute("SELECT id FROM schedules WHERE name = ?", (schedule_name,))
                schedule_id = cursor.fetchone()
                
                if not schedule_id:
                    logger.warning(f"No schedule found with name: {schedule_name}")
                    return None
                    
                # Get entries for this schedule
                cursor.execute("""
                    SELECT 
                        position as Cycle,
                        cycle_type as CycleType,
                        start_temp as StartTemp,
                        end_temp as EndTemp,
                        duration as CycleTime,
                        notes as Notes
                    FROM schedule_entries 
                    WHERE schedule_id = ?
                    ORDER BY position
                """, (schedule_id[0],))
                
                entries = []
                for row in cursor.fetchall():
                    entries.append({
                        'Cycle': row[0] + 1,  # Convert 0-based position to 1-based cycle
                        'CycleType': row[1],
                        'StartTemp': row[2],
                        'EndTemp': row[3],
                        'CycleTime': row[4],
                        'Notes': row[5] if row[5] else ''
                    })
                
                return entries
                
        except Exception as e:
            logger.error(f"Error loading schedule '{schedule_name}': {e}", exc_info=True)
            return None

    @classmethod
    def diagnose_database(cls):
        """Temporary diagnostic method to check database state."""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                
                # List all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                logger.info(f"Existing tables: {tables}")
                
                # Check schedules table
                cursor.execute("SELECT * FROM schedules;")
                schedules = cursor.fetchall()
                logger.info(f"Existing schedules: {schedules}")
                
                # Check schedule_entries
                cursor.execute("SELECT * FROM schedule_entries;")
                entries = cursor.fetchall()
                logger.info(f"Existing entries: {entries}")
                
        except Exception as e:
            logger.error(f"Diagnostic error: {e}", exc_info=True)