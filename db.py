import sqlite3


def init_db():
    """
    Creates the database file and tables if they do not exist yet
    """
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            user_id INTEGER PRIMARY KEY,
            salary REAL,
            save_amount REAL,
            salary_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            category TEXT,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()


def set_budget(user_id: int, salary: float, save_amount: float, salary_date: str):
    """
    Saves or updates the user's budget settings
    """
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO budget (user_id, salary, save_amount, salary_date)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            salary = excluded.salary,
            save_amount = excluded.save_amount,
            salary_date = excluded.salary_date
    """, (user_id, salary, save_amount, salary_date))

    conn.commit()
    conn.close()


def get_budget(user_id: int):
    """
    Returns the user's budget settings (or None if they do not exist yet)
    """
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()

    cursor.execute("SELECT salary, save_amount, salary_date FROM budget WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    conn.close()
    return result  # e.g. (80000.0, 20000.0, "2026-08-01") or None


def add_expense(user_id: int, amount: float, category: str, date: str):
    """
    Adds a new expense
    """
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses (user_id, amount, category, date)
        VALUES (?, ?, ?, ?)
    """, (user_id, amount, category, date))

    conn.commit()
    conn.close()


def get_expenses(user_id: int):
    """
    Returns a list of all expenses for the user
    """
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()

    cursor.execute("SELECT amount, category, date FROM expenses WHERE user_id = ?", (user_id,))
    result = cursor.fetchall()

    conn.close()
    return result  # list of tuples, e.g. [(500.0, "coffee", "2026-07-15"), ...]


def get_total_spent(user_id: int):
    """
    Returns the sum of all expenses for the user
    """
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()[0]

    conn.close()
    return result or 0  # if there are no expenses yet, SUM returns None — replace with 0
