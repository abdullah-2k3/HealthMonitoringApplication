from flask import Flask, render_template, redirect, url_for, request, session, flash
import pyodbc
import json
from datetime import datetime
from flask import jsonify

app = Flask(__name__)
app.secret_key = "hello"


# To remove the browser cache once logged out
@app.after_request
def add_cache_control(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


conn_str = "Driver={SQL Server};Server=DESKTOP-5REV9KP\SQLEXPRESS;Database=HealthMonitoringSystem"

conn = pyodbc.connect(conn_str)


def fetch_data_from_table(table_name):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name}")

    table_data = cursor.fetchall()

    columns = [column[0] for column in cursor.description]

    cursor.close()
    conn.close()

    return table_data, columns


def fetch_data_with_query(table_name, row_id, _=None):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        if _ == None:
            query = f"SELECT * FROM {table_name} WHERE id = ?"
        else:
            query = f"SELECT * FROM {table_name} WHERE {_} = ?"
        cursor.execute(query, (row_id,))

        table_data = cursor.fetchall()

        if not table_data:
            print(f"No row found with id {row_id}")

        columns = [column[0] for column in cursor.description]

        return table_data, columns
    except pyodbc.Error as e:
        print(f"Error fetching data: {e}")
        return None, None
    finally:
        cursor.close()
        conn.close()


def get_doctor_patients(id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        query = f"SELECT * FROM patients where id in (select patientid from appointments where doctorid = ?)"

        cursor.execute(query, (id,))

        table_data = cursor.fetchall()

        if not table_data:
            print(f"No row found with id {id}")
            table_data = ()

        columns = [column[0] for column in cursor.description]

        return table_data, columns
    except pyodbc.Error as e:
        print(f"Error fetching data: {e}")
        return None, None
    finally:
        cursor.close()
        conn.close()


def delete_row(table_name, row_id, _=None):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        if _ == None:
            _ = "id"
        delete_query = f"DELETE FROM {table_name} WHERE {_} = ?"
        cursor.execute(delete_query, (row_id,))
        conn.commit()
        return True
        if cursor.rowcount == 0:
            flash("Row not found", "error")
        else:
            flash("Row deleted successfully", "warning")
    except pyodbc.Error as e:
        print(f"Error deleting row: {e}")
        flash(str(e), "error")
        return False
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
        return True
    except pyodbc.Error as e:
        print(f"Error adding row: {e}")
        flash("An error occurred while adding the row", "error")
        flash(str(e))
        return False
    finally:
        cursor.close()
        conn.close()


def update_row(table_name, row_data, row_id, _=None):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

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
            return

        set_clause = ", ".join([f"{column} = ?" for column in row_data.keys()])

        if _ is None:
            update_query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
        else:
            update_query = f"UPDATE {table_name} SET {set_clause} WHERE {_} = ?"

        values = list(row_data.values()) + [row_id]

        cursor.execute(update_query, tuple(values))
        conn.commit()

        if cursor.rowcount == 0:
            flash("ID not found.", "error")
        else:
            flash(f"{columns} updated", "success")
    except pyodbc.Error as e:
        flash("An error occurred while updating the row", "error")
        flash(str(e), "warning")
    except ValueError as ve:
        print(f"ValueError: {ve}")
        flash("Row ID is missing.", "error")
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
            data, cols = fetch_data_with_query(
                "patienthealth", session["id"], "patient_id"
            )
            if len(data) == 0:
                data = (1, 2)
            return render_template("p_dashboard.html", data=data)

        elif role == "doctor":
            patients, cols = get_doctor_patients(session["id"])
            appointments, cols = fetch_data_with_query(
                "appointments", session["id"], "doctorid"
            )
            doctor, col = fetch_data_with_query("doctors", session["id"])
            locations = doctor[0][4].split()
            data = {
                "patients": len(patients),
                "appointments": len(appointments),
                "locations": len(locations),
            }
            return render_template("d_dashboard.html", data=data)

        elif role == "admin":
            doctors, col = fetch_data_from_table("doctors")
            patients, col = fetch_data_from_table("patients")
            appointments, col = fetch_data_from_table("appointments")
            users, col = fetch_data_from_table("users")

            data = {
                "doctors": len(doctors),
                "patients": len(patients),
                "appointments": len(appointments),
                "users": len(users),
            }

            return render_template("a_dashboard.html", data=data)
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    return render_template("login.html")


@app.context_processor
def inject_variables():
    if "username" in session and "role" in session:
        return dict(role=session["role"], username=session["username"])
    dummy = {"role": "role", "username": "username"}
    return dummy


@app.route("/notification_count", methods=["GET"])
def notification_count():
    data, cols = fetch_data_with_query("notifications", session["id"], "userid")
    count = sum(1 for notification in data if notification[3] == "new") if data else 0
    return jsonify({"count": count})


@app.route("/reset_notification_count", methods=["POST"])
def reset_notification_count():
    update_notification_status(session["id"])
    count = 0
    return "Count reset successfully", 200


def update_notification_status(user_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    try:
        query = "UPDATE notifications SET status = 'Viewed' WHERE userid = ? AND status = 'New'"
        cursor.execute(query, (user_id,))
        conn.commit()
    except pyodbc.Error as e:
        print(f"Error updating notification status: {e}")
    finally:
        cursor.close()
        conn.close()


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_patient")
def register_patient():
    return render_template("register_patient.html")


@app.route("/register_doctor")
def register_doctor():
    return render_template("register_doctor.html")


@app.route("/handle_register_patient", methods=["POST"])
def handle_register_patient():

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    contact = request.form["contact"]
    name = request.form["name"]
    gender = request.form["gender"]
    age = request.form["age"]

    user_data = {
        "username": username,
        "password": password,
        "role": "patient",
        "email": email,
        "contact": contact,
    }
    patient_data = {
        "id": 0,
        "name": name,
        "gender": gender,
        "age": age,
        "healthStatus": "Null",
    }

    if not add_row("users", user_data):
        flash("Could not register", "error")
        return redirect("/register")

    id = get_id("users", "username", username)
    patient_data["id"] = id
    if not add_row("patients", patient_data):
        flash("Could not register", "error")
    else:
        flash("You have been registered", "success")
    return redirect("/register_patient")


@app.route("/handle_register_doctor", methods=["POST"])
def handle_register_doctor():

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    contact = request.form["contact"]
    name = request.form["name"]
    qualification = request.form["qualification"]
    specialization = request.form["specialization"]
    location = request.form["locations"]

    user_data = {
        "username": username,
        "password": password,
        "role": "doctor",
        "email": email,
        "contact": contact,
    }
    id = 0
    doctor_data = {
        "id": id,
        "name": name,
        "qualification": qualification,
        "specialization": specialization,
        "location": location,
        "charges": 1500,
    }

    if not add_row("users", user_data):
        flash("Could not register", "error")
        return redirect("/register")

    id = get_id("users", "username", username)
    doctor_data["id"] = id
    if not add_row("doctors", doctor_data):
        flash("Could not register", "error")
    else:
        flash("You have been registered", "success")
    return redirect("/register_doctor")


@app.route("/profile")
def profile():
    if "username" in session and "role" in session:
        role = session["role"]
        data, col = fetch_data_with_query("users", session["id"])
        if role == "patient":
            patient_data, col = fetch_data_with_query("patients", session["id"])
            if not patient_data:
                patient_data = (1, 2, 3)
            return render_template("p_profile.html", user=data, patient=patient_data)
        elif role == "doctor":
            doctor_data, col = fetch_data_with_query("doctors", session["id"])
            return render_template("d_profile.html", user=data, doctor=doctor_data)
        elif role == "admin":
            return render_template("a_profile.html", user=data)
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/update_admin_profile", methods=["POST"])
def update_user_profile():

    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    contact = request.form.get("contact")
    confirm_password = request.form.get("confirm-pass")

    if password:
        if password != confirm_password:
            flash("Enter correct confirmation password to update", "warning")
            return redirect("/profile")

    id = session["id"]
    data = {
        "username": username,
        "password": password,
        "email": email,
        "contact": contact,
    }

    update_row("users", data, id)

    return redirect("/profile")


@app.route("/update_doctor_profile", methods=["POST"])
def update_doctor_profile():

    update_user_profile()

    name = request.form["name"]
    qualification = request.form["qualification"]
    specialization = request.form["specialization"]
    location = request.form["locations"]

    data = {
        "name": name,
        "qualification": qualification,
        "specialization": specialization,
        "location": location,
    }

    id = session["id"]
    update_row("doctors", data, id)

    return redirect("/profile")


@app.route("/update_patient_profile", methods=["POST"])
def update_patient_profile():

    update_user_profile()

    name = request.form["name"]
    age = request.form["age"]
    gender = request.form["gender"]
    health = request.form["health"]

    data = {
        "name": name,
        "age": age,
        "gender": gender,
        "health": health,
    }

    id = session["id"]
    update_row("patients", data, id)

    return redirect("/profile")


@app.route("/viewappointments")
def viewappointments():
    data, columns = fetch_data_with_query("appointments", session["id"], "patientID")
    if data == ():
        flash("You have no appointments", "info")
    return render_template("p_viewappointments.html", data=data, columns=columns)


@app.route("/cancel_appointment", methods=["POST"])
def cancel_appointment():
    id = session["id"]
    role = get_user_role(id)
    column = "patientid"
    if role == "doctor":
        column = "doctorid"

    data = {"Status": "canceled"}

    update_row("appointments", data, id, column)

    appointment_data, col = fetch_data_with_query("appointments", id, column)

    notification = {
        "userid": id,
        "notification": f"You cancelled your appointment on {appointment_data[0][4]} at {appointment_data[0][5][:8]}",
        "status": "New",
    }

    add_row("notifications", notification)

    return redirect("/viewappointments")


@app.route("/appointment")
def appointment():
    if "username" in session and "role" in session:
        role = session["role"]
        if role == "patient":
            data, columns = fetch_data_from_table("doctors")
            return render_template("p_appointment.html", data=data)
        elif role == "doctor":
            data, columns = fetch_data_with_query(
                "appointments", session["id"], "DoctorID"
            )
            if data == ():
                flash("You have no appointments")
            return render_template("d_appointment.html", data=data, columns=columns)
        elif role == "admin":
            data, columns = fetch_data_from_table("appointments")
            return render_template("a_appointment.html", data=data, columns=columns)
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


import pyodbc


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


@app.route("/handle_appointment_booking", methods=["POST"])
def handle_appointment_booking():

    patient_id = int(session["id"])
    doctor = request.form["doctor"]
    location = request.form["location"]
    date = request.form["date"]
    time = request.form["time"]
    details = request.form["details"]

    doctor_id = get_id("doctors", "name", doctor)
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
        "Fee": 1500,
        "details": details,
        "Status": "pending",
    }

    action = request.form.get("action")

    if action == "add":
        if add_row("appointments", appointment_data):
            flash("Appointment has been booked", "success")

    return redirect("/appointment")


@app.route("/handle_appointment_update", methods=["POST"])
def handle_appointment_update():
    appointment_id = request.form["id"]
    patient = request.form["patient"]
    doctor = request.form["doctor"]
    location = request.form["location"]
    date = request.form["date"]
    time = request.form["time"]
    details = request.form["details"]
    fee = request.form["fee"]
    status = request.form["status"]

    date = str(datetime.strptime(date, "%Y-%m-%d").date())
    time = str(datetime.strptime(time, "%H:%M").time())

    appointment_data = {
        "patientid": patient,
        "doctorid": doctor,
        "location": location,
        "date": date,
        "time": time,
        "details": details,
        "Fee": fee,
        "Status": status,
    }

    update_row("appointments", appointment_data, appointment_id, "AppointmentID")

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
            patients_data, columns = get_doctor_patients(session["id"])

            return render_template(
                "d_patients.html", data=patients_data, columns=columns
            )
        elif role == "admin":
            patients_data, columns = fetch_data_from_table("Patients")
            return render_template(
                "a_patients.html", data=patients_data, columns=columns
            )

    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/handle_patient_action", methods=["POST"])
def handle_patient_action():

    action = request.form.get("action")

    username = request.form.get("username")
    password = request.form.get("password")
    patient_name = request.form.get("patient_name")
    email = request.form.get("email")
    contact = request.form.get("contact")
    age = request.form.get("age")
    gender = request.form.get("gender")
    health = request.form.get("health")

    user_data = {}

    if username:
        user_data["username"] = username
    if password:

        user_data["password"] = password

    user_data["role"] = "patient"

    if email:
        user_data["email"] = email
    if contact:
        user_data["contact"] = contact

    patient_id = get_id("users", "username", username)

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
        patient_id = get_id("users", "username", username)
        patient_data["id"] = patient_id
        add_row("patients", patient_data)
        flash("Patient has been added", "success")

    elif action == "update":
        id = request.form.get("id")
        if not id:
            flash("Enter ID.", "error")
        elif get_user_role(id) != "patient":
            flash("Wrong ID", "warning")
        else:
            update_row("patients", patient_data, id)
            user_data["role"] = None
            update_row("users", user_data, id)

    elif action == "delete":
        id = request.form.get("id")
        if not id:
            flash("Enter ID.", "error")
        elif get_user_role(id) != "patient":
            flash("Wrong ID", "warning")
        else:
            if delete_row("users", id):
                flash("Patient has been removed", "warning")
            else:
                flash("Could not remove Patient", "warning")

    return redirect("/patients")


@app.route("/doctors")
def doctors():
    if "username" in session and "role" in session:
        role = session["role"]
        doctors_data, columns = fetch_data_from_table("doctors")
        if role == "patient":
            return render_template(
                "p_doctors.html", doctors=doctors_data, columns=columns
            )
        elif role == "admin":
            return render_template("a_doctors.html", data=doctors_data, columns=columns)
    else:
        flash("Please login to access this page", "error")
        return redirect(url_for("login"))


@app.route("/handle_doctor_action", methods=["POST"])
def handle_doctor_action():

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
        "username": username,
        "password": password,
        "role": "doctor",
        "email": email,
        "contact": contact,
    }

    doctor_id = get_id("users", "username", username)

    doctor_data = {
        "id": doctor_id,
        "name": doctor_name,
        "qualification": qualification,
        "specialization": specialization,
        "location": locations,
        "charges": 1500,
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
        doctor_data["id"] = get_id("users", "username", username)
        add_row("doctors", doctor_data)
        flash("Doctor has been added", "success")

    elif action == "update":
        id = request.form.get("id")
        if not id:
            flash("Enter ID.", "error")
        elif get_user_role(id) != "doctor":
            flash("Wrong ID", "warning")
        else:
            update_row("users", user_data, id)
            update_row("doctors", doctor_data, id)

    elif action == "delete":
        id = request.form.get("id")
        if not id:
            flash("Enter ID.", "error")
        elif get_user_role(id) != "doctor":
            flash("Wrong ID", "warning")
        else:
            if delete_row("users", id):
                flash("Doctor has been removed", "warning")
            else:
                flash("Could not remove doctor", "warning")

    return redirect("/doctors")


@app.route("/suggestions")
def suggestions():
    data, col = fetch_data_from_table("suggestions")
    return render_template("suggestions.html", users=data)


@app.route("/post_suggestion", methods=["POST"])
def post_suggestion():

    username = session["username"]
    message = request.form["message"]
    subject = request.form["subject"]

    data = {"username": username, "subject": subject, "suggestion": message}

    if add_row("suggestions", data):
        flash("Suggestion has been posted", "success")

    return redirect("/suggestions")


@app.route("/resources")
def resources():
    if "username" in session and "role" in session:
        data, col = fetch_data_from_table("suggestions")
        return render_template("resources.html", users=data)
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/faq")
def faq():
    if "username" in session and "role" in session:
        return render_template("faq.html")
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/notifications")
def notifications():
    if "username" in session and "role" in session:
        data, cols = fetch_data_with_query("notifications", session["id"], "userid")
        return render_template("notifications.html", data=data)
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
