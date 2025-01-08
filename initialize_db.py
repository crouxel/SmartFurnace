import sqlite3

def run_sql_file(filename):
    conn = sqlite3.connect('SmartFurnace.db')
    cursor = conn.cursor()
    with open(filename, 'r') as sql_file:
        sql_script = sql_file.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_sql_file('A2.sql')