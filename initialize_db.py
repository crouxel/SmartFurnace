# filepath: /c:/Users/crouxel/AppData/Documents/PROJECTS/SmartFurnace/initialize_db.py
import sqlite3

# Connect to the database
conn = sqlite3.connect('SmartFurnace.db')
cursor = conn.cursor()

# Create the A2 table
cursor.execute('''
CREATE TABLE IF NOT EXISTS A2 (
  Id INTEGER PRIMARY KEY,
  Cycle INTEGER NOT NULL,
  StartTemp INTEGER NOT NULL,
  EndTemp INTEGER NOT NULL,
  CycleType TEXT NOT NULL,
  CycleTime TEXT NOT NULL
)
''')

# Insert values into the A2 table
cursor.execute('''
INSERT INTO A2 (Id, Cycle, StartTemp, EndTemp, CycleType, CycleTime)
VALUES (1, 1, 22, 649, 'ramp', '40 minutes'),
       (2, 2, 649, 649, 'soak', '60 minutes')
''')

# Commit the changes and close the connection
conn.commit()
conn.close()