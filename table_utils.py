import sqlite3
from PyQt5.QtWidgets import QMenu, QAction

def fetch_tables():
    try:
        conn = sqlite3.connect('SmartFurnace.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except sqlite3.OperationalError as e:
        print(f"Error fetching tables: {e}")
        return []

def on_table_select(combo, label, plot_widget):
    selected_table = combo.currentText()
    if selected_table == "Add Schedule":
        open_add_table_window()
    else:
        label.setText(f"Selected table: {selected_table}")
        # Import regenerate_graph from Main.py
        from Main import regenerate_graph
        regenerate_graph(plot_widget, selected_table)

def show_context_menu(combo, label):
    menu = QMenu()
    edit_action = QAction("Edit Table", combo)
    delete_action = QAction("Delete Table", combo)
    add_action = QAction("Add Schedule", combo)

    # Connect actions to functions
    edit_action.triggered.connect(lambda: edit_table(combo.currentText()))
    delete_action.triggered.connect(lambda: delete_table(combo.currentText()))
    add_action.triggered.connect(open_add_table_window)

    # Add actions to the menu
    menu.addAction(edit_action)
    menu.addAction(delete_action)
    menu.addSeparator()
    menu.addAction(add_action)
    return menu

def edit_table(table_name):
    # Placeholder function for editing a table
    print(f"Edit table: {table_name}")

def delete_table(table_name):
    # Placeholder function for deleting a table
    print(f"Delete table: {table_name}")

def open_add_table_window():
    # Placeholder function for adding a new table
    print("Open add table window")