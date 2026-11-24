
from flask import Blueprint, request, jsonify
import sqlite3
import os
import math

group = Blueprint("group", __name__)


# ==================================================
# DATABASE LOCATION
# ==================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE = os.path.join(
    BASE_DIR,
    "database",
    "expense_splitter.db"
)


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ==================================================
# VALIDATE JSON
# ==================================================

def get_json_data():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None

    return data


# ==================================================
# VALIDATE POSITIVE INTEGER
# ==================================================

def valid_id(value):

    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


# ==================================================
# VALIDATE AMOUNT
# ==================================================

def valid_amount(value):

    try:

        amount = float(value)

        if not math.isfinite(amount) or amount <= 0:
            return None

        return round(amount, 2)

    except (TypeError, ValueError):

        return None


# ==================================================
# SPLIT AMOUNT EQUALLY
# ==================================================

def calculate_equal_split(amount, members):

    total_paise = round(amount * 100)

    count = len(members)

    base_share = total_paise // count

    remainder = total_paise % count

    shares = []

    for index, member in enumerate(members):

        share = base_share

        if index < remainder:
            share += 1

        shares.append({
            "user_id": member["user_id"],
            "amount_owed": share / 100
        })

    return shares


# ==================================================
# CREATE GROUP
# ==================================================

@group.route("/groups", methods=["POST"])
def create_group():

    data = get_json_data()

    if data is None:
        return jsonify({"message": "Invalid request data"}), 400

    name = data.get("name")
    created_by = data.get("created_by")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"message": "Group name is required"}), 400

    try:
        created_by = int(created_by)
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid user ID"}), 400

    if created_by <= 0:
        return jsonify({"message": "Invalid user ID"}), 400

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE id = ?",
            (created_by,)
        )

        if cursor.fetchone() is None:
            return jsonify({"message": "User does not exist"}), 404

        cursor.execute(
            """
            INSERT INTO groups (name, created_by)
            VALUES (?, ?)
            """,
            (name.strip(), created_by)
        )

        group_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO group_members (group_id, user_id)
            VALUES (?, ?)
            """,
            (group_id, created_by)
        )

        connection.commit()

        return jsonify({
            "message": "Group created successfully",
            "group_id": group_id
        }), 201

    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 500

    finally:

        connection.close()


# ==================================================
# GET GROUPS FOR A USER
# ==================================================

@group.route("/groups/<int:user_id>", methods=["GET"])
def get_user_groups(user_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                g.id,
                g.name,
                g.created_by,
                g.created_at
            FROM groups g
            JOIN group_members gm
                ON g.id = gm.group_id
            WHERE gm.user_id = ?
            ORDER BY g.id DESC
            """,
            (user_id,)
        )

        groups = [dict(row) for row in cursor.fetchall()]

        return jsonify({
            "groups": groups
        }), 200

    finally:

        connection.close()


# ==================================================
# ADD MEMBER TO GROUP
# ==================================================

@group.route("/groups/<int:group_id>/members", methods=["POST"])
def add_member(group_id):

    data = get_json_data()

    if data is None:
        return jsonify({"message": "Invalid request"}), 400

    user_id = data.get("user_id")

    if not valid_id(user_id):
        return jsonify({"message": "Valid user ID is required"}), 400

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM groups WHERE id = ?",
            (group_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"message": "Group not found"}), 404

        cursor.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"message": "User not found"}), 404

        cursor.execute(
            """
            SELECT id
            FROM group_members
            WHERE group_id = ? AND user_id = ?
            """,
            (group_id, user_id)
        )

        if cursor.fetchone():
            return jsonify({
                "message": "User is already a member of this group"
            }), 400

        cursor.execute(
            """
            INSERT INTO group_members (group_id, user_id)
            VALUES (?, ?)
            """,
            (group_id, user_id)
        )

        connection.commit()

        return jsonify({
            "message": "Member added successfully"
        }), 201

    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 500

    finally:

        connection.close()


# ==================================================
# GET MEMBERS OF A GROUP
# ==================================================

@group.route("/groups/<int:group_id>/members", methods=["GET"])
def get_group_members(group_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM groups WHERE id = ?",
            (group_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"message": "Group not found"}), 404

        cursor.execute(
            """
            SELECT
                u.id,
                u.name,
                u.email
            FROM group_members gm
            JOIN users u
                ON gm.user_id = u.id
            WHERE gm.group_id = ?
            ORDER BY u.name
            """,
            (group_id,)
        )

        members = [dict(row) for row in cursor.fetchall()]

        return jsonify({
            "members": members
        }), 200

    finally:

        connection.close()


# ==================================================
# REMOVE MEMBER FROM GROUP
# ==================================================

@group.route(
    "/groups/<int:group_id>/members/<int:user_id>",
    methods=["DELETE"]
)
def remove_member(group_id, user_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, created_by
            FROM groups
            WHERE id = ?
            """,
            (group_id,)
        )

        existing_group = cursor.fetchone()

        if existing_group is None:
            return jsonify({"message": "Group not found"}), 404

        if existing_group["created_by"] == user_id:
            return jsonify({
                "message": "Group creator cannot be removed"
            }), 400

        cursor.execute(
            """
            SELECT id
            FROM group_members
            WHERE group_id = ? AND user_id = ?
            """,
            (group_id, user_id)
        )

        if cursor.fetchone() is None:
            return jsonify({
                "message": "Member not found in this group"
            }), 404

        # Do not remove members who still have unsettled expenses.
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM expense_splits es
            JOIN expenses e ON es.expense_id = e.id
            WHERE e.group_id = ?
            AND es.user_id = ?
            """,
            (group_id, user_id)
        )

        if cursor.fetchone()["total"] > 0:

            return jsonify({
                "message": "Cannot remove this member because expense records exist. Settle or clear their expenses first."
            }), 400

        cursor.execute(
            """
            DELETE FROM group_members
            WHERE group_id = ? AND user_id = ?
            """,
            (group_id, user_id)
        )

        connection.commit()

        return jsonify({
            "message": "Member removed successfully"
        }), 200

    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 500

    finally:

        connection.close()


# ==================================================
# ADD EXPENSE
# ==================================================

@group.route("/groups/<int:group_id>/expenses", methods=["POST"])
def add_expense(group_id):

    data = get_json_data()

    if data is None:
        return jsonify({"message": "Invalid request"}), 400

    description = data.get("description")
    amount = valid_amount(data.get("amount"))
    paid_by = data.get("paid_by")

    category = data.get("category")
    expense_date = data.get("expense_date")

    if not isinstance(description, str) or not description.strip():
        return jsonify({"message": "Description is required"}), 400

    if amount is None:
        return jsonify({"message": "Invalid expense amount"}), 400

    if not valid_id(paid_by):
        return jsonify({"message": "Valid payer ID is required"}), 400

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM groups WHERE id = ?",
            (group_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"message": "Group not found"}), 404

        cursor.execute(
            """
            SELECT id
            FROM group_members
            WHERE group_id = ? AND user_id = ?
            """,
            (group_id, paid_by)
        )

        if cursor.fetchone() is None:
            return jsonify({
                "message": "Payer must be a member of this group"
            }), 400

        cursor.execute(
            """
            INSERT INTO expenses (
                group_id,
                description,
                amount,
                paid_by,
                category,
                expense_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                group_id,
                description.strip(),
                amount,
                paid_by,
                category,
                expense_date
            )
        )

        expense_id = cursor.lastrowid

        connection.commit()

        return jsonify({
            "message": "Expense added successfully",
            "expense_id": expense_id
        }), 201

    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 500

    finally:

        connection.close()


# ==================================================
# SPLIT EXPENSE EQUALLY
# ==================================================

@group.route("/expenses/<int:expense_id>/split", methods=["POST"])
def split_expense(expense_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT group_id, amount
            FROM expenses
            WHERE id = ?
            """,
            (expense_id,)
        )

        expense = cursor.fetchone()

        if expense is None:
            return jsonify({"message": "Expense not found"}), 404

        group_id = expense["group_id"]

        cursor.execute(
            """
            SELECT id
            FROM expense_splits
            WHERE expense_id = ?
            LIMIT 1
            """,
            (expense_id,)
        )

        if cursor.fetchone():
            return jsonify({
                "message": "This expense has already been split"
            }), 400

        cursor.execute(
            """
            SELECT user_id
            FROM group_members
            WHERE group_id = ?
            ORDER BY user_id
            """,
            (group_id,)
        )

        members = cursor.fetchall()

        if not members:
            return jsonify({
                "message": "No members found in this group"
            }), 400

        shares = calculate_equal_split(
            float(expense["amount"]),
            members
        )

        for share in shares:

            cursor.execute(
                """
                INSERT INTO expense_splits (
                    expense_id,
                    user_id,
                    amount_owed
                )
                VALUES (?, ?, ?)
                """,
                (
                    expense_id,
                    share["user_id"],
                    share["amount_owed"]
                )
            )

        connection.commit()

        return jsonify({
            "message": "Expense split successfully",
            "total_amount": float(expense["amount"]),
            "number_of_members": len(members),
            "shares": shares
        }), 200

    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 500

    finally:

        connection.close()


# ==================================================
# GET ALL EXPENSES OF A GROUP
# ==================================================

@group.route("/groups/<int:group_id>/expenses", methods=["GET"])
def get_group_expenses(group_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM groups WHERE id = ?",
            (group_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"message": "Group not found"}), 404

        cursor.execute(
            """
            SELECT
                e.id,
                e.description,
                e.amount,
                e.category,
                e.expense_date,
                e.paid_by,
                u.name AS paid_by_name
            FROM expenses e
            JOIN users u
                ON e.paid_by = u.id
            WHERE e.group_id = ?
            ORDER BY e.id DESC
            """,
            (group_id,)
        )

        expenses = [dict(row) for row in cursor.fetchall()]

        return jsonify({
            "expenses": expenses
        }), 200

    finally:

        connection.close()


# ==================================================
# CALCULATE GROUP BALANCES
# ==================================================

@group.route("/groups/<int:group_id>/balances", methods=["GET"])
def get_group_balances(group_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM groups WHERE id = ?",
            (group_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"message": "Group not found"}), 404

        cursor.execute(
            """
            SELECT
                u.id,
                u.name,
                u.upi_id,

                COALESCE((
                    SELECT SUM(e.amount)
                    FROM expenses e
                    WHERE e.group_id = ?
                    AND e.paid_by = u.id
                ), 0) AS total_paid,

                COALESCE((
                    SELECT SUM(es.amount_owed)
                    FROM expense_splits es
                    JOIN expenses e
                        ON es.expense_id = e.id
                    WHERE e.group_id = ?
                    AND es.user_id = u.id
                ), 0) AS total_owed,

                COALESCE((
                    SELECT SUM(p.amount)
                    FROM payments p
                    WHERE p.group_id = ?
                    AND p.paid_by = u.id
                    AND p.status = 'COMPLETED'
                ), 0) AS payments_sent,

                COALESCE((
                    SELECT SUM(p.amount)
                    FROM payments p
                    WHERE p.group_id = ?
                    AND p.paid_to = u.id
                    AND p.status = 'COMPLETED'
                ), 0) AS payments_received

            FROM group_members gm
            JOIN users u
                ON gm.user_id = u.id
            WHERE gm.group_id = ?
            ORDER BY u.name
            """,
            (
                group_id,
                group_id,
                group_id,
                group_id,
                group_id
            )
        )

        members = cursor.fetchall()

        balances = []

        for member in members:

            total_paid = round(member["total_paid"], 2)
            total_owed = round(member["total_owed"], 2)

            payments_sent = round(member["payments_sent"], 2)
            payments_received = round(member["payments_received"], 2)

            balance = round(
                total_paid
                - total_owed
                + payments_sent
                - payments_received,
                2
            )

            if balance > 0.01:
                status = "You Get"

            elif balance < -0.01:
                status = "You Owe"

            else:
                status = "Settled"

            balances.append({

                "user_id": member["id"],
                "name": member["name"],
                "upi_id": member["upi_id"] or "",

                "total_paid": total_paid,
                "total_owed": total_owed,

                "payments_sent": payments_sent,
                "payments_received": payments_received,

                "balance": balance,
                "status": status

            })

        return jsonify({
            "balances": balances
        }), 200

    finally:

        connection.close()


# ==================================================
# GET GROUP DETAILS
# ==================================================

@group.route("/groups/<int:group_id>/details", methods=["GET"])
def get_group_details(group_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, name, created_by, created_at
            FROM groups
            WHERE id = ?
            """,
            (group_id,)
        )

        group_data = cursor.fetchone()

        if group_data is None:
            return jsonify({"message": "Group not found"}), 404

        return jsonify(dict(group_data)), 200

    finally:

        connection.close()


# ==================================================
# GET GROUP PAYMENTS
# ==================================================

@group.route("/groups/<int:group_id>/payments", methods=["GET"])
def get_group_payments(group_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM groups WHERE id = ?",
            (group_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"message": "Group not found"}), 404

        cursor.execute(
            """
            SELECT
                p.*,
                sender.name AS paid_by_name,
                receiver.name AS paid_to_name
            FROM payments p

            LEFT JOIN users sender
                ON p.paid_by = sender.id

            LEFT JOIN users receiver
                ON p.paid_to = receiver.id

            WHERE p.group_id = ?

            ORDER BY p.created_at DESC
            """,
            (group_id,)
        )

        payments = [dict(row) for row in cursor.fetchall()]

        return jsonify({
            "payments": payments
        }), 200

    finally:

        connection.close()


# ==================================================
# ADD PAYMENT
# ==================================================

@group.route("/groups/<int:group_id>/payments", methods=["POST"])
def add_payment(group_id):

    data = get_json_data()

    if data is None:
        return jsonify({"message": "Invalid request"}), 400

    paid_by = data.get("paid_by")
    paid_to = data.get("paid_to")

    amount = valid_amount(data.get("amount"))

    payment_method = data.get("payment_method", "UPI")
    transaction_id = data.get("transaction_id")

    if not valid_id(paid_by) or not valid_id(paid_to):
        return jsonify({"message": "Invalid payment members"}), 400

    if paid_by == paid_to:
        return jsonify({
            "message": "Sender and receiver cannot be the same"
        }), 400

    if amount is None:
        return jsonify({"message": "Invalid payment amount"}), 400

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM groups WHERE id = ?",
            (group_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"message": "Group not found"}), 404

        cursor.execute(
            """
            SELECT user_id
            FROM group_members
            WHERE group_id = ?
            AND user_id IN (?, ?)
            """,
            (group_id, paid_by, paid_to)
        )

        members = cursor.fetchall()

        if len(members) != 2:
            return jsonify({
                "message": "Both users must belong to this group"
            }), 400

        cursor.execute(
            """
            INSERT INTO payments (
                group_id,
                paid_by,
                paid_to,
                amount,
                payment_method,
                status,
                transaction_id
            )
            VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
            """,
            (
                group_id,
                paid_by,
                paid_to,
                amount,
                payment_method,
                transaction_id
            )
        )

        payment_id = cursor.lastrowid

        connection.commit()

        return jsonify({
            "message": "Payment recorded successfully",
            "payment_id": payment_id,
            "status": "PENDING"
        }), 201

    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 500

    finally:

        connection.close()


# ==================================================
# CONFIRM PAYMENT
# ==================================================

@group.route(
    "/groups/<int:group_id>/payments/<int:payment_id>/confirm",
    methods=["POST"]
)
def confirm_payment(group_id, payment_id):

    data = get_json_data()

    if data is None:
        return jsonify({"message": "Invalid request"}), 400

    receiver_id = data.get("receiver_id")

    if not valid_id(receiver_id):
        return jsonify({
            "message": "Valid receiver ID is required"
        }), 400

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, paid_to, status
            FROM payments
            WHERE id = ? AND group_id = ?
            """,
            (payment_id, group_id)
        )

        payment = cursor.fetchone()

        if payment is None:
            return jsonify({"message": "Payment not found"}), 404

        if payment["paid_to"] != receiver_id:
            return jsonify({
                "message": "Only the receiver can confirm this payment"
            }), 403

        if payment["status"] != "PENDING":
            return jsonify({
                "message": "Payment is already processed"
            }), 400

        cursor.execute(
            """
            UPDATE payments
            SET status = 'COMPLETED',
                paid_at = CURRENT_TIMESTAMP
            WHERE id = ?
            AND group_id = ?
            AND status = 'PENDING'
            """,
            (payment_id, group_id)
        )

        if cursor.rowcount != 1:
            return jsonify({
                "message": "Payment could not be confirmed"
            }), 400

        connection.commit()

        return jsonify({
            "message": "Payment confirmed successfully",
            "status": "COMPLETED"
        }), 200

    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 500

    finally:

        connection.close()


# ==================================================
# DELETE ALL EXPENSES AND PAYMENTS
# ==================================================

@group.route("/expenses/clear-all", methods=["DELETE"])
def clear_all_expenses():

    data = get_json_data()

    if data is None or data.get("confirm") != "DELETE ALL EXPENSES":
        return jsonify({
            "message": "Confirmation required"
        }), 400

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("DELETE FROM expense_splits")
        cursor.execute("DELETE FROM expenses")
        cursor.execute("DELETE FROM payments")

        connection.commit()

        return jsonify({
            "message": "All expenses and payment records deleted successfully"
        }), 200

    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 500

    finally:

        connection.close()


# ==================================================
# DELETE INDIVIDUAL EXPENSE
# ==================================================

@group.route(
    "/expenses/<int:expense_id>",
    methods=["DELETE"]
)
def delete_expense(expense_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM expenses WHERE id = ?",
            (expense_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"message": "Expense not found"}), 404

        cursor.execute(
            "DELETE FROM expense_splits WHERE expense_id = ?",
            (expense_id,)
        )

        cursor.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )

        connection.commit()

        return jsonify({
            "message": "Expense deleted successfully"
        }), 200

    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 500

    finally:

        connection.close()


# ==================================================
# EDIT INDIVIDUAL EXPENSE
# ==================================================

@group.route(
    "/expenses/<int:expense_id>",
    methods=["PUT"]
)
def edit_expense(expense_id):

    data = get_json_data()

    if data is None:
        return jsonify({"message": "Invalid request"}), 400

    description = data.get("description")
    amount = valid_amount(data.get("amount"))

    category = data.get("category")
    expense_date = data.get("expense_date")
    paid_by = data.get("paid_by")

    if not isinstance(description, str) or not description.strip():
        return jsonify({"message": "Description is required"}), 400

    if amount is None:
        return jsonify({"message": "Invalid expense amount"}), 400

    if not valid_id(paid_by):
        return jsonify({"message": "Valid payer ID is required"}), 400

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, group_id
            FROM expenses
            WHERE id = ?
            """,
            (expense_id,)
        )

        expense = cursor.fetchone()

        if expense is None:
            return jsonify({"message": "Expense not found"}), 404

        group_id = expense["group_id"]

        cursor.execute(
            """
            SELECT id
            FROM group_members
            WHERE group_id = ? AND user_id = ?
            """,
            (group_id, paid_by)
        )

        if cursor.fetchone() is None:
            return jsonify({
                "message": "Payer must belong to this group"
            }), 400

        # Check whether the expense was already split
        cursor.execute(
            """
            SELECT id
            FROM expense_splits
            WHERE expense_id = ?
            LIMIT 1
            """,
            (expense_id,)
        )

        was_split = cursor.fetchone() is not None

        # Do not silently reset existing paid split records
        if was_split:

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM expense_splits
                WHERE expense_id = ?
                AND is_paid = 1
                """,
                (expense_id,)
            )

            if cursor.fetchone()["total"] > 0:
                return jsonify({
                    "message": "This expense has paid splits and cannot be edited."
                }), 400

        cursor.execute(
            """
            UPDATE expenses
            SET description = ?,
                amount = ?,
                category = ?,
                expense_date = ?,
                paid_by = ?
            WHERE id = ?
            """,
            (
                description.strip(),
                amount,
                category,
                expense_date,
                paid_by,
                expense_id
            )
        )

        # Recalculate shares if expense was already split
        if was_split:

            cursor.execute(
                """
                SELECT user_id
                FROM group_members
                WHERE group_id = ?
                ORDER BY user_id
                """,
                (group_id,)
            )

            members = cursor.fetchall()

            if not members:
                raise ValueError("No group members available")

            shares = calculate_equal_split(amount, members)

            cursor.execute(
                "DELETE FROM expense_splits WHERE expense_id = ?",
                (expense_id,)
            )

            for share in shares:

                cursor.execute(
                    """
                    INSERT INTO expense_splits (
                        expense_id,
                        user_id,
                        amount_owed,
                        is_paid
                    )
                    VALUES (?, ?, ?, 0)
                    """,
                    (
                        expense_id,
                        share["user_id"],
                        share["amount_owed"]
                    )
                )

        connection.commit()

        return jsonify({
            "message": "Expense updated successfully",
            "splits_updated": was_split
        }), 200

    except ValueError as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 400

    except sqlite3.Error as error:

        connection.rollback()

        return jsonify({"message": str(error)}), 500

    finally:

        connection.close()
