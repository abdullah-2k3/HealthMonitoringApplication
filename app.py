from flask import Flask, render_template, redirect, url_for, request, session, flash
import pyodbc
import json
from datetime import datetime
from flask import jsonify

app = Flask(__name__)
app.secret_key = "hello"


@app.after_request
def add_cache_control(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


conn_str = "Driver={SQL Server};Server=DESKTOP-5REV9KP\SQLEXPRESS;Database=HealthMonitoringSystem"

conn = pyodbc.connect(conn_str)


def fetch_data_from_table(table_name):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Execute SQL query to fetch data from the specified table
    cursor.execute(f"SELECT * FROM {table_name}")

    # Fetch data
    table_data = cursor.fetchall()

    # Fetch column headers
    columns = [column[0] for column in cursor.description]

    cursor.close()
    conn.close()

    return table_data, columns


def delete_row(table_name, row_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        delete_query = f"DELETE FROM {table_name} WHERE id = ?"
        cursor.execute(delete_query, (row_id,))
        conn.commit()
        if cursor.rowcount == 0:
            flash("Row not found", "error")
        else:
            flash("Row deleted successfully", "warning")
    except pyodbc.Error as e:
        print(f"Error deleting row: {e}")
        flash("An error occurred while deleting the row", "error")
    finally:
        cursor.close()
        conn.close()


def add_row(table_name, row_data):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        columns = ", ".join(row_data.keys())
        placeholders = ", ".join(["?"] * len(row_data))
        insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"

        values = [v if v is not None else "" for v in row_data.values()]
        cursor.execute(insert_query, tuple(values))

        conn.commit()
        flash("Row added successfully", "success")
    except pyodbc.Error as e:
        print(f"Error adding row: {e}")
        flash("An error occurred while adding the row", "error")
        flash(str(e))
    finally:
        cursor.close()
        conn.close()


def update_row(table_name, row_data):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        row_id = row_data.get("id", None)
        if row_id is None:
            raise ValueError("Row ID is missing.")

        # Remove the row ID and None values from the dictionary
        row_data = {
            key: value
            for key, value in row_data.items()
            if value is not None and key != "id"
        }

        # If no non-None values are left after filtering, return without updating
        if not row_data:
            flash("No non-None values provided for update.", "warning")
            return

        set_clause = ", ".join([f"{column} = ?" for column in row_data.keys()])

        update_query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"

        values = list(row_data.values()) + [row_id]

        cursor.execute(update_query, tuple(values))
        conn.commit()

        if cursor.rowcount == 0:
            flash("ID not found.", "error")
        else:
            flash("Row updated successfully", "success")
    except pyodbc.Error as e:
        print(f"Error updating row: {e}")
        flash("An error occurred while updating the row", "error")
    except ValueError as ve:
        print(f"ValueError: {ve}")
        flash("Row ID is missing in the row_data dictionary.", "error")
    except pyodbc.ProgrammingError as pe:
        print(f"ProgrammingError: {pe}")
        flash("Row ID not found in the table.", "error")
    finally:
        cursor.close()
        conn.close()


def authenticate_user(username, password):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = "SELECT id, role FROM users WHERE username = ? AND [password] = ?"
        cursor.execute(query, (username, password))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return user_data if user_data else None
    except Exception as e:
        flash(str(e), "warning")
        return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        data = authenticate_user(username, password)

        if data:
            id = data[0]
            role = data[1]
        else:
            flash("Invalid username or password", "error")
            return render_template("login.html")

        session["username"] = username
        session["role"] = role
        session["id"] = id
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" in session and "role" in session:
        role = session["role"]
        if role == "patient":
            return render_template("p_dashboard.html")
        elif role == "doctor":
            return render_template("d_dashboard.html")
        elif role == "admin":
            return render_template("a_dashboard.html")
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/patient-data")
def patient_data():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Patients")

    # Get column names from cursor description
    columns = [column[0] for column in cursor.description]

    # Fetch all rows
    rows = cursor.fetchall()

    # Convert rows to a list of dictionaries
    data = []
    for row in rows:
        data.append(dict(zip(columns, row)))

    # Return column headers and data as JSON
    return jsonify(columns=columns, data=data)


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        user = request.form["nm"]
        session["user"] = user
        return redirect(url_for("user"))
    else:
        if "user" in session:
            return redirect(url_for("user"))

        return render_template("register.html")


@app.route("/profile")
def profile():
    if "username" in session and "role" in session:
        role = session["role"]
        if role == "patient":
            return render_template("p_profile.html")
        elif role == "doctor":
            return render_template("d_profile.html")
        elif role == "admin":
            return render_template("a_profile.html")
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/viewdata")
def viewdata():
    return render_template("p_viewdata.html")


@app.route("/appointment")
def appointment():
    if "username" in session and "role" in session:
        role = session["role"]
        if role == "patient":
            data, columns = fetch_data_from_table("doctors")
            return render_template("p_appointment.html", data=data)
        elif role == "doctor":
            return render_template("d_appointment.html")
        elif role == "admin":
            data, columns = fetch_data_from_table("appointments")
            return render_template("a_appointment.html", data=data, columns=columns)
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


def get_id(table, name):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = f"SELECT id FROM {table} WHERE name = ?"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return int(result[0]) if result else None
    except Exception as e:
        print("Error:", e)
        return None


@app.route("/handle_appointment_action", methods=["POST"])
def handle_appointment_action():

    patient_id = int(session["id"])
    doctor = request.form["doctor"]
    location = request.form["location"]
    date = request.form["date"]
    time = request.form["time"]
    details = request.form["details"]

    if not date:
        flash("Select a date.", "error")
        return redirect("/appointment")

    if not time:
        flash("Select a time.", "error")
        return redirect("/appointment")

    if not location:
        flash("Select a location.", "error")
        return redirect("/appointment")

    doctor_id = get_id("doctors", doctor)
    if not doctor_id:
        flash("Doctor not found.", "error")
        return redirect("/appointment")

    date = str(datetime.strptime(date, "%Y-%m-%d").date())
    time = str(datetime.strptime(time, "%H:%M").time())

    appointment_data = {
        "patientid": patient_id,
        "doctorid": doctor_id,
        "location": location,
        "date": date,
        "time": time,
        "details": details,
        "Status": "pending",
    }

    action = request.form.get("action")

    if action == "add":
        add_row("appointments", appointment_data)

    elif action == "delete":
        # delete_row("patients", patient_id)
        delete_row("users", patient_id)

    return redirect("/appointment")


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


@app.route("/users")
def users():
    if "username" in session:
        user_data, columns = fetch_data_from_table("users")
        return render_template("a_users.html", data=user_data, columns=columns)


@app.route("/patients")
def patients():
    if "username" in session and "role" in session:
        role = session["role"]
        if role == "doctor":
            return render_template("d_patients.html")
        elif role == "admin":
            patients_data, columns = fetch_data_from_table("Patients")
            user_data, columns2 = fetch_data_from_table("users")
            return render_template(
                "a_patients.html", data=patients_data, columns=columns
            )

    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/handle_patient_action", methods=["POST"])
def handle_patient_action():

    patient_id = request.form.get("patient_id")

    if not patient_id:
        flash("Please enter the patient ID.", "error")
        return redirect("/patients")

    action = request.form.get("action")

    username = request.form.get("username")
    password = request.form.get("password")
    patient_name = request.form.get("patient_name")
    email = request.form.get("email")
    contact = request.form.get("contact")
    age = request.form.get("age")
    gender = request.form.get("gender")
    health = request.form.get("health")

    if age:
        age = int(age)

    patient_id = int(patient_id)

    user_data = {"id": patient_id}

    if username:
        user_data["username"] = username
    if password:
        user_data["password"] = password

    user_data["role"] = "patient"

    if email:
        user_data["email"] = email
    if contact:
        user_data["contact"] = contact

    patient_data = {
        "id": patient_id,
        "name": patient_name,
        "gender": gender,
        "age": age,
        "healthStatus": health,
    }

    if action == "add":
        if not (
            username
            and password
            and patient_name
            and age
            and gender
            and email
            and contact
            and health
        ):
            flash("Please fill in all fields.", "error")
            return redirect("/patients")
        add_row("users", user_data)
        add_row("patients", patient_data)

    elif action == "update":
        update_row("patients", patient_data)
        if username and password:
            update_row("users", user_data)
        elif username or password:
            flash(
                "User details not updated. Please enter both username and password to update."
            )

    elif action == "delete":
        # delete_row("patients", patient_id)
        delete_row("users", patient_id)

    return redirect("/patients")


@app.route("/doctors")
def doctors():
    doctors_data, columns = fetch_data_from_table("doctors")
    return render_template("a_doctors.html", data=doctors_data, columns=columns)


@app.route("/handle_doctor_action", methods=["POST"])
def handle_doctor_action():

    doctor_id = request.form.get("doctor_id")

    if not doctor_id:
        flash("Please enter the doctor ID.", "error")
        return redirect("/doctors")

    action = request.form.get("action")

    username = request.form.get("username")
    password = request.form.get("password")
    doctor_name = request.form.get("doctor_name")
    qualification = request.form.get("qualification")
    specialization = request.form.get("specialization")
    locations = request.form.get("locations")
    email = request.form.get("email")
    contact = request.form.get("contact")

    user_data = {
        "id": doctor_id,
        "username": username,
        "password": password,
        "role": "patient",
        "email": email,
        "contact": contact,
    }

    doctor_data = {
        "id": doctor_id,
        "name": doctor_name,
        "qualification": qualification,
        "specialization": specialization,
        "location": locations,
    }

    if action == "add":
        if not (
            doctor_name
            and qualification
            and specialization
            and locations
            and email
            and contact
        ):
            flash("Please fill in all fields.", "error")
            return redirect("/doctors")
        add_row("users", user_data)
        add_row("doctors", doctor_data)

    elif action == "update":
        update_row("doctors", doctor_data)

    elif action == "delete":
        delete_row("doctors", doctor_id)
        delete_row("users", doctor_id)

    return redirect("/doctors")


@app.route("/suggestions")
def suggestions():
    return render_template("suggestions.html")


if __name__ == "__main__":
    app.run(debug=True)
