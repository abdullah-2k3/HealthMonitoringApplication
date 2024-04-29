from flask import redirect, request, session, flash, Blueprint
import crud_operation as crud
from datetime import datetime, timedelta

action_routes = Blueprint("routes", __name__)


@action_routes.route("/handle_register_patient", methods=["POST"])
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

    if not crud.add_row("users", user_data):
        flash("Could not register", "error")
        return redirect("/register")

    id = crud.get_id("users", "username", username)
    patient_data["id"] = id
    if not crud.add_row("patients", patient_data):
        flash("Could not register", "error")
    else:
        flash("You have been registered", "success")
    return redirect("/register_patient")


@action_routes.route("/handle_register_doctor", methods=["POST"])
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

    if not crud.add_row("users", user_data):
        flash("Could not register", "error")
        return redirect("/register")

    id = crud.get_id("users", "username", username)
    doctor_data["id"] = id
    if not crud.add_row("doctors", doctor_data):
        flash("Could not register", "error")
    else:
        flash("You have been registered", "success")
    return redirect("/register_doctor")


@action_routes.route("/handle_appointment_request", methods=["POST"])
def handle_appointment_request():

    patient_id = int(session["id"])
    doctor = request.form["doctor"]
    location = request.form["location"]
    date = request.form["date"]
    time = request.form["time"]
    details = request.form["details"]

    doctor_id = crud.get_id("doctors", "name", doctor)
    if not doctor_id:
        flash("Doctor not found.", "error")
        return redirect("/appointment")

    date = str(datetime.strptime(date, "%Y-%m-%d").date())
    time = str(datetime.strptime(time, "%H:%M").time())

    existing_appointments, cols = crud.fetch_data_with_query(
        "appointments", doctor_id, "doctorid"
    )

    if any(appt[4] == date and appt[5] == time for appt in existing_appointments):
        flash("Appointment not available in this slot.", "warning")
        return redirect("/appointment")

    appointment_data = {
        "patientid": patient_id,
        "doctorid": doctor_id,
        "location": location,
        "date": date,
        "time": time,
        "Fee": 1500,
        "details": details,
        "Status": "not confirmed",
    }

    if crud.add_row("appointments", appointment_data):
        flash(
            "Appointment has been requested, you will be notified when it is confirmed.",
            "success",
        )

    message = f"Your appointment on {date} at {time} has been requested. You will be notified here when it is confirmed."

    patient_notification_data = {
        "userid": patient_id,
        "notification": message,
        "status": "new",
    }

    crud.add_row("notifications", patient_notification_data)

    message = f"You have an appointment request from patient id {patient_id} on {date} at {time}."

    doctor_notification_data = {
        "userid": doctor_id,
        "notification": message,
        "status": "new",
    }

    crud.add_row("notifications", doctor_notification_data)

    return redirect("/appointment")


@action_routes.route("/handle_appointment_update", methods=["POST"])
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

    crud.update_row("appointments", appointment_data, appointment_id, "AppointmentID")

    return redirect("/appointment")


@action_routes.route("/handle_patient_action", methods=["POST"])
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

    patient_id = crud.get_id("users", "username", username)

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
        crud.add_row("users", user_data)
        patient_id = crud.get_id("users", "username", username)
        patient_data["id"] = patient_id
        crud.add_row("patients", patient_data)
        flash("Patient has been added", "success")

    elif action == "update":
        id = request.form.get("id")
        if not id:
            flash("Enter ID.", "error")
        elif crud.get_user_role(id) != "patient":
            flash("Wrong ID", "warning")
        else:
            crud.update_row("patients", patient_data, id)
            user_data["role"] = None
            crud.update_row("users", user_data, id)

    elif action == "delete":
        id = request.form.get("id")
        if not id:
            flash("Enter ID.", "error")
        elif crud.get_user_role(id) != "patient":
            flash("Wrong ID", "warning")
        else:
            if crud.delete_row("users", id):
                flash("Patient has been removed", "warning")
            else:
                flash("Could not remove Patient", "warning")

    return redirect("/patients")


@action_routes.route("/handle_doctor_action", methods=["POST"])
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

    doctor_id = crud.get_id("users", "username", username)

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
        crud.add_row("users", user_data)
        doctor_data["id"] = crud.get_id("users", "username", username)
        crud.add_row("doctors", doctor_data)
        flash("Doctor has been added", "success")

    elif action == "update":
        id = request.form.get("id")
        if not id:
            flash("Enter ID.", "error")
        elif crud.get_user_role(id) != "doctor":
            flash("Wrong ID", "warning")
        else:
            user_data["role"] = None
            crud.update_row("users", user_data, id)
            crud.update_row("doctors", doctor_data, id)

    elif action == "delete":
        id = request.form.get("id")
        if not id:
            flash("Enter ID.", "error")
        elif crud.get_user_role(id) != "doctor":
            flash("Wrong ID", "warning")
        else:
            if crud.delete_row("users", id):
                flash("Doctor has been removed", "warning")
            else:
                flash("Could not remove doctor", "warning")

    return redirect("/doctors")


@action_routes.route("/reset_notification_count", methods=["POST"])
def reset_notification_count():
    crud.update_notification_status(session["id"])
    count = 0
    return "Count reset successfully", 200


@action_routes.route("/update_patient_profile", methods=["POST"])
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
        "healthStatus": health,
    }

    id = session["id"]
    crud.update_row("patients", data, id)

    return redirect("/profile")


@action_routes.route("/update_admin_profile", methods=["POST"])
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

    crud.update_row("users", data, id)

    return redirect("/profile")


@action_routes.route("/update_doctor_profile", methods=["POST"])
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
    crud.update_row("doctors", data, id)

    return redirect("/profile")


@action_routes.route("/cancel_appointment", methods=["POST"])
def cancel_appointment():
    id = request.form["appointmentid"]
    userid = session["id"]

    data = {"Status": "canceled"}

    crud.update_row("appointments", data, id, "appointmentid")

    appointment_data, col = crud.fetch_data_with_query(
        "appointments", id, "appointmentid"
    )
    patientid = appointment_data[0][1]
    doctorid = appointment_data[0][2]
    message = f"Your appointment on {appointment_data[0][4]} at {appointment_data[0][5][:8]} is canceled by User ID {userid}."

    send_appointment_notification(doctorid, patientid, message)

    if session["role"] == "patient":
        return redirect("/viewappointments")

    return redirect("/appointment")


@action_routes.route("/confirm_appointment", methods=["POST"])
def confirm_appointment():
    id = request.form["appointmentid"]
    userid = session["id"]

    data = {"Status": "confirmed"}

    crud.update_row("appointments", data, id, "appointmentid")

    appointment_data, col = crud.fetch_data_with_query(
        "appointments", id, "appointmentid"
    )
    patientid = appointment_data[0][1]
    doctorid = appointment_data[0][2]
    message = f"Your appointment on {appointment_data[0][4]} at {appointment_data[0][5][:8]} is confirmed."

    send_appointment_notification(doctorid, patientid, message)

    if session["role"] == "patient":
        return redirect("/viewappointments")

    return redirect("/appointment")


def send_appointment_notification(doctorid, patientid, message):
    notification = {
        "userid": doctorid,  # doctorid
        "notification": message,
        "status": "new",
    }
    crud.add_row("notifications", notification)

    notification["userid"] = patientid  # patientid
    crud.add_row("notifications", notification)


@action_routes.route("/post_suggestion", methods=["POST"])
def post_suggestion():
    username = session["username"]
    message = request.form["message"]
    subject = request.form["subject"]

    data = {"username": username, "subject": subject, "suggestion": message}

    if crud.add_row("suggestions", data):
        flash("Suggestion has been posted", "success")

    return redirect("/suggestions")


@action_routes.route("/add_patient_health_data", methods=["POST"])
def add_patient_health_data():
    patientid = session["id"]
    datetime_str = request.form["datetime"]
    datetime_str = datetime_str.replace("T", " ")
    bloodpressure = request.form["bloodpressure"]
    heartrate = request.form["heartrate"]
    temprature = request.form["temprature"]
    weight = request.form["weight"]
    height = request.form["height"]
    symptoms = request.form["symptoms"]
    diagnosis = request.form["diagnosis"]
    treatment = request.form["treatment"]
    medications = request.form["medications"]
    notes = request.form["notes"]
    sleeptime = request.form["sleeptime"]

    if not bloodpressure:
        bloodpressure = "-"
    if not heartrate:
        heartrate = "-"
    if not temprature:
        temprature = 0
    if not weight:
        weight = 0
    if not height:
        height = 0
    if not symptoms:
        symptoms = "-"
    if not diagnosis:
        diagnosis = "-"
    if not treatment:
        treatment = "-"
    if not medications:
        medications = "-"
    if not notes:
        notes = "-"
    if not sleeptime:
        sleeptime = 0

    data = {
        "patientid": patientid,
        "datetime": datetime_str,
        "bloodpressure": bloodpressure,
        "heartrate": heartrate,
        "temprature": temprature,
        "weight": weight,
        "height": height,
        "symptoms": symptoms,
        "diagnosis": diagnosis,
        "treatment": treatment,
        "medications": medications,
        "notes": notes,
        "sleeptime": sleeptime,
    }

    if crud.add_row("patienthealth", data):
        flash("Health data has been uploaded", "success")
    else:
        flash("Could not enter patient data", "danger")

    return redirect("/health_records")
