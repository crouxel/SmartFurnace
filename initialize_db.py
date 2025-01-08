# filepath: /c:/Users/crouxel/AppData/Documents/PROJECTS/SmartFurnace/initialize_db.py
import sqlite3

# Read the SQL commands from the A2.sql file
with open('A2.sql', 'r') as file:
    sql_commands = file.read()

# Connect to the database
conn = sqlite3.connect('SmartFurnace.db')
cursor = conn.cursor()

# Execute the SQL commands
cursor.executescript(sql_commands)

# Commit the changes and close the connection
conn.commit()
conn.close()