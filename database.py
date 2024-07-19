import sqlite3


DATABASE = "health_monitoring_system.db"


db = sqlite3.connect(DATABASE, check_same_thread=False, timeout=10)


def close_connection(exception):
    if db is not None:
        db.close()


def init_db():

    cursor = db.cursor()
    cursor.executescript(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE,
        password VARCHAR(50),
        role VARCHAR(50),
        email VARCHAR(100) UNIQUE,
        contact VARCHAR(20)
    );
    
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100),
        qualification VARCHAR(100),
        specialization VARCHAR(100),
        location VARCHAR(100),
        charges FLOAT,
        FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY,
        name VARCHAR(50),
        gender VARCHAR(10),
        age INTEGER,
        health_status VARCHAR(50),
        FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS PatientHealth (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        date_time DATETIME,
        blood_pressure VARCHAR(20),
        heart_rate INTEGER,
        temperature_F DECIMAL(5,2),
        weight_lbs DECIMAL(5,2),
        height_inches DECIMAL(5,2),
        symptoms VARCHAR(1500),
        diagnosis VARCHAR(1500),
        treatment VARCHAR(1000),
        medications VARCHAR(1000),
        notes VARCHAR(1500),
        sleeptime INTEGER,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    );
    
    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        location VARCHAR(50),
        date DATE,
        time TIME,
        fee FLOAT,
        details VARCHAR(1000),
        status VARCHAR(50),
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );
    
    CREATE TABLE IF NOT EXISTS suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50),
        subject VARCHAR(100),
        suggestion VARCHAR(3000),
        FOREIGN KEY (username) REFERENCES users(username)
    );
    
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        notification VARCHAR(1000),
        status VARCHAR(10),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """
    )
    db.commit()


def add_admin():
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO USERS  (username, password, role, email, contact) VALUES ('admin1', 'password1', 'admin', 'admin1@email.com', '012345677')"
    )
    db.commit()


def get_users():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()

    return users if users else "None"


def alter_patients():
    cursor = db.cursor()
    cursor.execute("ALTER TABLE patients ADD COLUMN HealthStatus VARCHAR(100)")
    db.commit()
    print("Column added")
