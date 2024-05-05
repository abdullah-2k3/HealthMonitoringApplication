from flask import Flask, render_template, redirect, url_for, request, session, flash
import crud_operation as crud
from handle_form_actions import action_routes
from socket_events import socketio
from flask import jsonify
import json


app = Flask(__name__)
app.secret_key = "hello"

app.register_blueprint(action_routes)
socketio.init_app(app)


# To remove the browser cache once logged out
@app.after_request
def add_cache_control(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_patient")
def register_patient():
    return render_template("register_patient.html")


@app.route("/register_doctor")
def register_doctor():
    return render_template("register_doctor.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        data = crud.authenticate_user(username, password)

        if data:
            id = data[0][0]
            role = data[0][1]
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
            id = session["id"]
            query = f"SELECT * FROM patienthealth WHERE patient_id = {id} ORDER BY date_time"
            data, cols = crud.execute_fetch_query(query)
            if not data:
                data = [0, 0]
            return render_template("p_dashboard.html", data=data)

        elif role == "doctor":
            patients, cols = crud.get_doctor_patients(session["id"])
            appointments, cols = crud.fetch_data_with_query(
                "appointments", session["id"], "doctorid"
            )
            doctor, col = crud.fetch_data_with_query("doctors", session["id"])
            locations = doctor[0][4].split(",")
            data = {
                "patients": len(patients),
                "appointments": len(appointments),
                "locations": len(locations),
            }
            return render_template("d_dashboard.html", data=data)

        elif role == "admin":
            doctors, col = crud.fetch_data_from_table("doctors")
            patients, col = crud.fetch_data_from_table("patients")
            appointments, col = crud.fetch_data_from_table("appointments")
            users, col = crud.fetch_data_from_table("users")

            data = {
                "doctors": len(doctors),
                "patients": len(patients),
                "appointments": len(appointments),
                "users": len(users),
            }

            return render_template("a_dashboard.html", data=data)
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/health_visualization")
def health_visualization():
    if "username" in session and "role" in session:
        id = session["id"]
        query = f"SELECT * FROM patienthealth WHERE patient_id = {id} ORDER BY record_id DESC"
        data, cols = crud.execute_fetch_query(query)

        weight = [row[6] for row in data]
        height = [row[7] for row in data]
        bp = [row[3] for row in data]
        heart_rate = [row[4] for row in data]
        sleeptime = [row[13] for row in data]
        temp = [row[5] for row in data]
        datetime = [row[2] for row in data]

        chart_data = {
            "height": height,
            "weight": weight,
            "bloodpressure": bp,
            "heartrate": heart_rate,
            "datetime": datetime,
            "temprature": temp,
            "sleeptime": sleeptime,
        }
        return render_template("p_visualization.html", chart_data=chart_data)

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
    data, cols = crud.fetch_data_with_query("notifications", session["id"], "userid")
    count = (
        sum(1 for notification in data if notification[3].lower() == "new")
        if data
        else 0
    )
    return jsonify({"count": count})


@app.route("/profile")
def profile():
    if "username" in session and "role" in session:
        role = session["role"]
        data, col = crud.fetch_data_with_query("users", session["id"])
        if role == "patient":
            patient_data, col = crud.fetch_data_with_query("patients", session["id"])
            return render_template("p_profile.html", user=data, patient=patient_data)
        elif role == "doctor":
            doctor_data, col = crud.fetch_data_with_query("doctors", session["id"])
            return render_template("d_profile.html", user=data, doctor=doctor_data)
        elif role == "admin":
            return render_template("a_profile.html", user=data)
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/viewappointments")
def viewappointments():
    if "username" in session and "role" in session:
        role = session["role"]
        if role == "patient":
            query = f"SELECT * FROM appointments WHERE patientid = ? ORDER BY appointmentid DESC"
            data, cols = crud.execute_fetch_query(query, (session["id"],))
            if data == ():
                flash("You have no appointments", "info")
            return render_template("p_viewappointments.html", data=data, columns=cols)
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/appointment", methods=["GET", "POST"])
def appointment():
    if "username" in session and "role" in session:
        role = session["role"]
        if role == "patient":
            data, columns = crud.fetch_data_from_table("doctors")
            return render_template("p_appointment.html", data=data)
        elif role == "doctor":
            query = f"SELECT * FROM appointments WHERE doctorid = ? ORDER BY appointmentid DESC"
            data, cols = crud.execute_fetch_query(query, (session["id"],))
            if data == ():
                flash("You have no appointments")
            return render_template("d_appointment.html", data=data, columns=cols)
        elif role == "admin":
            data, columns = crud.fetch_data_from_table("appointments")
            return render_template("a_appointment.html", data=data, columns=columns)
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/users")
def users():
    if "username" in session:
        user_data, columns = crud.fetch_data_from_table("users")
        return render_template("a_users.html", data=user_data, columns=columns)


@app.route("/patients")
def patients():
    if "username" in session and "role" in session:
        role = session["role"]
        if role == "doctor":
            patients_data, columns = crud.get_doctor_patients(session["id"])

            return render_template(
                "d_patients.html", data=patients_data, columns=columns
            )
        elif role == "admin":
            patients_data, columns = crud.fetch_data_from_table("Patients")
            return render_template(
                "a_patients.html", data=patients_data, columns=columns
            )

    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/admins")
def admins():
    if "username" in session and "role" in session:
        query = "Select * from users Where role = 'admin'"
        admins_data, columns = crud.execute_fetch_query(query)
        return render_template("a_admins.html", data=admins_data, columns=columns)

    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/health_records")
def health_records():
    if "username" in session and "role" in session:
        data, columns = crud.fetch_data_with_query(
            "patienthealth", session["id"], "patient_id"
        )
        return render_template("p_health_records.html", data=data, columns=columns)

    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/doctors")
def doctors():
    if "username" in session and "role" in session:
        role = session["role"]
        doctors_data, columns = crud.fetch_data_from_table("doctors")
        if role == "patient":
            return render_template(
                "p_doctors.html", doctors=doctors_data, columns=columns
            )
        elif role == "admin":
            return render_template("a_doctors.html", data=doctors_data, columns=columns)
    else:
        flash("Please login to access this page", "error")
        return redirect(url_for("login"))


@app.route("/suggestions")
def suggestions():
    if "username" in session and "role" in session:
        data, col = crud.fetch_data_from_table("suggestions")
        return render_template("suggestions.html", users=data)

    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/resources")
def resources():
    if "username" in session and "role" in session:
        data, col = crud.fetch_data_from_table("suggestions")
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
        query = (
            f"SELECT * FROM notifications WHERE userid = ? ORDER BY notificationid DESC"
        )
        data, cols = crud.execute_fetch_query(query, (session["id"],))
        return render_template("notifications.html", data=data, role=session["role"])
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


@app.route("/chat")
def chat():
    if "username" in session and "role" in session:
        return render_template("chat.html", username=session["username"])
    flash("Please login to access this page", "error")
    return redirect(url_for("login"))


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=True)
