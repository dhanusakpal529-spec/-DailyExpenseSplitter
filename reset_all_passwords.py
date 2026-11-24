
import sqlite3
from getpass import getpass
from werkzeug.security import generate_password_hash

DATABASE = "database/expense_splitter.db"

print("===== RESET ALL USER PASSWORDS =====")

new_password = getpass("Enter the new common password: ")
confirm_password = getpass("Confirm the new password: ")

if not new_password:
    print("Password cannot be empty.")

elif new_password != confirm_password:
    print("Passwords do not match.")

else:
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    try:
        hashed_password = generate_password_hash(new_password)

        cursor.execute("""
            UPDATE users
            SET password = ?
        """, (hashed_password,))

        connection.commit()

        print(f"Successfully reset {cursor.rowcount} user passwords.")

    except sqlite3.Error as error:
        connection.rollback()
        print("Database error:", error)

    finally:
        connection.close()
