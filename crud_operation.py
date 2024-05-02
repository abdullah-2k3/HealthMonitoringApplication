from flask import flash
import pyodbc

conn_str = "Driver={SQL Server};Server=DESKTOP-5REV9KP\SQLEXPRESS;Database=HealthMonitoringSystem"


def execute_fetch_query(query, params=None):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        table_data = cursor.fetchall()

        if not table_data:
            print("No rows found.")

        columns = [column[0] for column in cursor.description]

        return table_data, columns
    except pyodbc.Error as e:
        print(f"Error executing query: {e}")
        return None, None
    finally:
        cursor.close()
        conn.close()


def fetch_data_from_table(table_name):
    query = f"SELECT * FROM {table_name}"
    return execute_fetch_query(query)


def fetch_data_with_query(table_name, row_id, _="id"):
    query = f"SELECT * FROM {table_name} WHERE {_} = ?"
    return execute_fetch_query(query, (row_id,))


def get_doctor_patients(id):
    query = f"SELECT DISTINCT * FROM patients where id in (select patientid from appointments where doctorid = ?)"
    return execute_fetch_query(query, (id,))


def execute_query(query, params=None):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        conn.commit()
        return True
    except pyodbc.Error as e:
        flash(f"Error executing query: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def add_row(table_name, row_data):
    try:
        columns = ", ".join(row_data.keys())
        placeholders = ", ".join(["?"] * len(row_data))
        insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"

        values = [v if v is not None else "" for v in row_data.values()]

        return execute_query(insert_query, tuple(values))
    except pyodbc.Error as e:
        print(f"Error adding row: {e}")
        return False


def update_row(table_name, row_data, row_id, _="id"):
    try:
        if row_id is None:
            raise ValueError("Row ID is missing.")

        row_data = {
            key: value
            for key, value in row_data.items()
            if value is not None and value != ""
        }
        columns = [key for key in row_data.keys()]

        if not row_data:
            return False

        set_clause = ", ".join([f"{column} = ?" for column in row_data.keys()])
        update_query = f"UPDATE {table_name} SET {set_clause} WHERE {_} = ?"

        values = list(row_data.values()) + [row_id]

        result = execute_query(update_query, tuple(values))

        if result:
            flash(f"{columns} updated", "success")
            return True

    except (pyodbc.Error, ValueError) as e:
        print(f"Error updating row: {e}")
        return False


def delete_row(table_name, row_id, _="id"):
    try:
        delete_query = f"DELETE FROM {table_name} WHERE {_} = ?"
        success = execute_query(delete_query, (row_id,))

        if success:
            return True
        else:
            return False
    except pyodbc.Error as e:
        flash(f"Error deleting row: {e}")
        return False


def authenticate_user(username, password):
    query = "SELECT id, role FROM users WHERE username = ? AND [password] = ?"
    data, cols = execute_fetch_query(query, (username, password))
    return data


def get_user_role(id):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = "SELECT role FROM users WHERE id = ?"
        cursor.execute(query, (id))
        role = str(cursor.fetchone()[0])
        cursor.close()
        conn.close()
        return role if role else None
    except Exception as e:
        flash("No record found", "warning")
        return None


def get_id(table, column, name):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = f"SELECT id FROM {table} WHERE {column} = ?"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return int(result[0]) if result else None
    except Exception as e:
        print("Error:", e)
        return None


def is_user_registered(id, role):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        user_check_query = "SELECT id FROM users WHERE id = ? AND role = ?"
        cursor.execute(user_check_query, (id, role))
        user_row = cursor.fetchone()

        if user_row is None:
            flash(
                f"Cannot add row: ID does not exist or is not assigned the role '{role}'.",
                "error",
            )
            return False

    except pyodbc.Error as e:
        print(f"Error adding row: {e}")
        flash("An error occurred while adding the row.", "error")
    finally:
        cursor.close()
        conn.close()
        return True


def update_notification_status(user_id):
    try:
        query = "UPDATE notifications SET status = 'Viewed' WHERE userid = ? AND status = 'New'"
        return execute_query(query, (user_id,))

    except pyodbc.Error as e:
        print(f"Error updating notification status: {e}")
        return False
