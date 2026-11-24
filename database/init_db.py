
import sqlite3
import os

# =====================================
# DATABASE LOCATION
# =====================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE = os.path.join(
    BASE_DIR,
    "database",
    "expense_splitter.db"
)


# =====================================
# DATABASE CONNECTION
# =====================================

def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    # Enable foreign key support
    connection.execute("PRAGMA foreign_keys = ON")

    # Return rows like dictionaries
    connection.row_factory = sqlite3.Row

    return connection


# =====================================
# CREATE DATABASE TABLES
# =====================================

def create_tables():

    # Make sure database folder exists
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

    connection = get_db_connection()

    cursor = connection.cursor()

    try:

        # =====================================
        # 1. USERS TABLE
        # =====================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            upi_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Add upi_id if it does not exist
        cursor.execute("PRAGMA table_info(users)")

        columns = [column["name"] for column in cursor.fetchall()]

        if "upi_id" not in columns:

            cursor.execute("""
            ALTER TABLE users
            ADD COLUMN upi_id TEXT
            """)


        # =====================================
        # 2. GROUPS TABLE
        # =====================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (created_by)
            REFERENCES users(id)
        )
        """)


        # =====================================
        # 3. GROUP MEMBERS TABLE
        # =====================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (group_id)
            REFERENCES groups(id),

            FOREIGN KEY (user_id)
            REFERENCES users(id),

            UNIQUE (group_id, user_id)
        )
        """)


        # =====================================
        # 4. EXPENSES TABLE
        # =====================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            paid_by INTEGER NOT NULL,
            category TEXT,
            expense_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (group_id)
            REFERENCES groups(id),

            FOREIGN KEY (paid_by)
            REFERENCES users(id)
        )
        """)


        # =====================================
        # 5. EXPENSE SPLITS TABLE
        # =====================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_splits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount_owed REAL NOT NULL,
            is_paid INTEGER DEFAULT 0,

            FOREIGN KEY (expense_id)
            REFERENCES expenses(id),

            FOREIGN KEY (user_id)
            REFERENCES users(id),

            UNIQUE (expense_id, user_id)
        )
        """)


        # =====================================
        # 6. PAYMENTS / SETTLEMENTS TABLE
        # =====================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            paid_by INTEGER NOT NULL,
            paid_to INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'UPI',
            status TEXT DEFAULT 'PENDING',
            transaction_id TEXT,
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (group_id)
            REFERENCES groups(id),

            FOREIGN KEY (paid_by)
            REFERENCES users(id),

            FOREIGN KEY (paid_to)
            REFERENCES users(id)
        )
        """)


        # =====================================
        # 7. CREATE INDEXES
        # =====================================

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_group_members_group
        ON group_members(group_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_group_members_user
        ON group_members(user_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_expenses_group
        ON expenses(group_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_expense_splits_expense
        ON expense_splits(expense_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_group
        ON payments(group_id)
        """)


        # =====================================
        # SAVE DATABASE
        # =====================================

        connection.commit()

        print("All database tables created successfully!")

    except sqlite3.Error as error:

        connection.rollback()

        print("Database Error:", error)

        raise

    finally:

        connection.close()


# =====================================
# RUN DIRECTLY
# =====================================

if __name__ == "__main__":

    create_tables()