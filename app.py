from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
from flask import request
from flask import redirect,session
from datetime import datetime, timedelta


app = Flask(__name__)


app.secret_key = "my_secret_key"


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()



class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    user_name = db.Column(db.String, nullable = False)
    user_email = db.Column(db.String, nullable = False)
    user_password = db.Column(db.String, nullable = False)
    user_role = db.Column(db.String, default = "patient")
    doctor_specialization = db.Column(db.Integer, db.ForeignKey('departments.department_id'), nullable = True)
    blacklist = db.Column(db.Boolean, default = False)
    department = db.relationship("Department", back_populates = "doctors")
    appointment_patient = db.relationship("Appointments", foreign_keys = "Appointments.patient_id", back_populates = "patients")
    appointment_doctor = db.relationship("Appointments", foreign_keys = "Appointments.doctor_id", back_populates = "doctors")
    available = db.relationship("Availability", back_populates = "doctor_availability")
    patient_treatment = db.relationship("Treatment", foreign_keys = "Treatment.patient_id", back_populates = "treatment_patient")
    doctor_treatment =  db.relationship("Treatment", foreign_keys = "Treatment.doctor_id", back_populates = "treatment_doctor")

class Department(db.Model):
    __tablename__ = 'departments'
    department_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    department_name = db.Column(db.String, nullable = False)
    description = db.Column(db.Text)
    doctors_registered = db.Column(db.String, unique = True)
    doctors= db.relationship("User", back_populates = "department")

class Appointments(db.Model):
    __tablename__ = "appointments"
    appointment_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.user_id'),nullable = False)
    doctor_id =  db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable = False)
    date = db.Column(db.String, nullable = False)
    time = db.Column(db.String, nullable = False)
    status = db.Column(db.String, nullable = False)
    patients = db.relationship("User", foreign_keys = [patient_id], back_populates = "appointment_patient")
    doctors = db.relationship("User", foreign_keys = [doctor_id], back_populates = "appointment_doctor")
    treatments = db.relationship("Treatment", back_populates = "appointment")

class Treatment(db.Model):
    __tablename__ = "treatment"
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.appointment_id'))
    treatment_id = db.Column(db.Integer, primary_key = True,  autoincrement = True)
    diagnosis = db.Column(db.String, nullable = False)
    prescription = db.Column(db.String, nullable = False)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.user_id'),nullable = False)
    doctor_id =  db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable = False)
    date = db.Column(db.String, nullable = False) 
    appointment = db.relationship("Appointments", back_populates = "treatments")
    treatment_patient = db.relationship("User", foreign_keys = [patient_id], back_populates = "patient_treatment")
    treatment_doctor = db.relationship("User", foreign_keys = [doctor_id], back_populates = "doctor_treatment")

class Availability(db.Model):
    __tablename__ = "available_doctors"
    availability_id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    doctor_id =  db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable = False)
    date = db.Column(db.String, nullable = False)
    time = db.Column(db.String, nullable = False)
    status = db.Column(db.String, nullable = False)
    doctor_availability = db.relationship("User", back_populates = "available")




@app.route("/")
def Index():
    return render_template("index.html") 

@app.route("/logout", methods = ["POST","GET"])
def Logout():
    session.clear()
    return render_template("index.html") 

@app.route("/sign_up", methods = ["POST","GET"])
def Sign_Up():
    error = None
    if request.method == "POST":
        user_name = request.form["user_name"]
        user_email = request.form["user_email"]
        user_password = request.form["user_password"] 

        existing_user = User.query.filter_by(user_email = user_email).first()

        if existing_user:
            error = "Email Already Exists" 
            return render_template("sign_up.html", error = error)
    
        new_user = User(user_name = user_name, user_email = user_email, user_password = user_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")

    return render_template("sign_up.html", error = error) 

@app.route("/login", methods = ["GET","POST"])
def Login():
    error = None
    if request.method == "POST":
        user_email = request.form["user_email"]
        user_password = request.form["user_password"]
        correct_email = User.query.filter_by(user_email = user_email).first()
        correct_password = User.query.filter_by(user_email = user_email,user_password = user_password).first()

        if correct_email:

            if correct_password and correct_email.user_role == "patient":
                if correct_email.blacklist:
                    error = "You are Blocked! Contact the Admin"
                    return render_template("index.html", error = error) 
                session["user_role"] = correct_email.user_role
                session["user_name"] = correct_email.user_name
                session["user_id"] = correct_email.user_id
                return redirect("/patient_dashboard")
        
            elif correct_password and correct_email.user_role == "doctor":
                if correct_email.blacklist:
                    error = "You are Blocked! Contact the Admin"
                    return render_template("index.html", error = error)
                session["user_role"] = correct_email.user_role
                session["user_name"] = correct_email.user_name
                session["user_id"] = correct_email.user_id
                return redirect("/doctor_dashboard")
        
            elif correct_password and correct_email.user_role == "admin":
                session["user_role"] = correct_email.user_role
                return redirect("/admin_dashboard")
            
            elif not correct_password:
                error = "Incorrect Password"

        else:
            error = "Account does not Exist"
            
    return render_template("login.html", error = error) 






@app.route("/patient_dashboard", methods = ["GET","POST"])
def Patient_Dashboard():
    if "user_role" not in session or session["user_role"] != "patient":
        error = "Login or Sign up to Access"
        return render_template("/index.html", error = error)
    
    user_id = session.get("user_id")
    appointments = Appointments.query.filter_by(patient_id = user_id, status = "Booked").all()

    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()
    return render_template("patient_dashboard.html",appointments = appointments, patients=patients, doctors=doctors, user_id = user_id, user_name = session.get("user_name"), departments = departments)

@app.route("/patient_dashboard/search", methods = ["GET","POST"])
def Patient_Search():
    searched = request.args.get("search","").strip()
    if searched == "":
        return redirect("/patient_dashboard")
    
    id = searched.isdigit()

    searched_doctors = User.query.filter(User.user_role == "doctor",((User.user_name.ilike(f"{searched}%")) | ((User.user_id == int(searched)) if id else False))).all()
    searched_departments = Department.query.filter((Department.department_name.ilike(f"{searched}%")) | ((Department.department_id == int(searched)) if id else False)).all()

    patients = User.query.filter_by(user_role = "patient").all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    departments = Department.query.all()

    return render_template("patient_dashboard.html", patients = patients, searched = searched, searched_doctors = searched_doctors, searched_departments = searched_departments, doctors = doctors, departments = departments, user_id = session.get("user_id"), user_name = session.get("user_name"))


@app.route("/patient_dashboard/history", methods = ["GET","POST"])
def Patient_View_History():
    patient_id = session.get("user_id")
    treatments = Treatment.query.filter(Treatment.patient_id == patient_id, Treatment.prescription != "Appointment cancelled", Treatment.prescription != "Appointment cancelled by Patient" ).all()
    return render_template("patient_view_history.html",treatments = treatments)
    
@app.route("/patient_dashboard/edit/<int:user_id>", methods = ["GET","POST"])
def Edit_Patient(user_id):
    patient = User.query.get(user_id)
    return render_template("edit_patient.html",patient=patient)


@app.route("/patient_dashboard/edit/edit_patient/<int:user_id>", methods = ["GET","POST"])
def Patient_Edit(user_id):
    error = None
    patient = User.query.get(user_id)
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()
    appointments = Appointments.query.filter_by(patient_id = user_id, status = "Booked").all()

    if request.method == "POST":
        patient.user_name = request.form["patient_name"]
        patient.user_email = request.form["patient_email"]
        patient.user_password = request.form["patient_password"]
        existing_user = User.query.filter(User.user_email == request.form["patient_email"], User.user_id != user_id).first()
        if existing_user:
            error = "Email Already Exist"
            return render_template("edit_patient.html",patient = patient, error = error)
        db.session.commit()
    return render_template("patient_dashboard.html", patients=patients, doctors=doctors, user_id = session.get("user_id"), user_name = session.get("user_name"), departments = departments, appointments =appointments)

@app.route("/patient_dashboard/patients_registered_doctor/<int:dept_id>", methods = ["GET","POST"])
def Patients_Registered_Doctors(dept_id):
    doctors = User.query.filter_by(user_role = "doctor", doctor_specialization = dept_id).all()
    department = Department.query.get(dept_id)
    departments = Department.query.all()
    return render_template("patients_registered_doctors.html", doctors=doctors,departments=departments,department=department)

@app.route("/patient_dashboard/patients_all_departments", methods = ["GET","POST"])
def Patient_All_Departments():
    departments = Department.query.all()
    return render_template("patients_all_departments.html", user_name = session.get("user_name"), departments = departments)

@app.route("/patient_dashboard/patients_registered_doctor/check_availability", methods = ["GET","POST"])
def Check_Availability():
   
    doctor_id = request.form.get("doctor_id") or request.args.get("doctor_id")
    doctor = User.query.get(doctor_id)
    department = Department.query.get(doctor.doctor_specialization)

    if request.method == "POST":
        date_selected = request.form.get("date_selected")
    else:
        date_selected = request.args.get("date_selected")

    availability = Availability.query.filter_by(doctor_id = doctor_id).all()

    slots_of_date = {}

    for slot in availability:
        slots_of_date.setdefault(slot.date, []).append(slot.time)

    date_list = sorted(slots_of_date.keys(), key = lambda d: datetime.strptime(d, "%d-%m-%Y"))

    for time in date_list:
        slots_of_date[time].sort()

  
    booked_appointments = Appointments.query.filter_by(doctor_id = doctor.user_id, status = "Booked").all()
    already_booked = set()

    for booked in booked_appointments:
        already_booked.add((booked.date, booked.time))

    return render_template("check_availability.html", date_selected = date_selected, doctor = doctor, department = department, dates = date_list, slots = slots_of_date.get(date_selected, []), already_booked = already_booked)

@app.route("/patient_dashboard/patients_registered_doctor/book_appointment", methods = ["GET","POST"])
def Book_Appointment():
    error = None
    patient_id = session.get("user_id")
    doctor_id = request.form.get("doctor_id") or request.args.get("doctor_id")
    time_selected = request.form.get("time")
    date_selected = request.form.get("date_selected") or request.args.get("date_selected")
  
    doctor = User.query.get(doctor_id)
    department = Department.query.get(doctor.doctor_specialization)
    department_id = doctor.doctor_specialization

    availability = Availability.query.filter_by(doctor_id = doctor_id).all()

    slots_of_date = {}

    for slot in availability:
        slots_of_date.setdefault(slot.date, []).append(slot.time)


    date_list = sorted(slots_of_date.keys(), key = lambda d: datetime.strptime(d, "%d-%m-%Y"))

    for time in date_list:
        slots_of_date[time].sort()

    booked_appointments = Appointments.query.filter_by(doctor_id = doctor.user_id, status = "Booked").all()
    already_booked = set()

    for booked in booked_appointments:
        already_booked.add((booked.date, booked.time))
    
    if request.method == "GET":
        return render_template("check_availability.html",doctor=doctor,department=department,dates=date_list,slots=slots_of_date.get(date_selected, []),date_selected=date_selected,already_booked=already_booked)
    
    if not date_selected or not time_selected:
        error = "Select Date and Time to Book Appointment"
        return render_template("check_availability.html", date_selected = date_selected, slots = slots_of_date.get(date_selected, []), doctor = doctor, department = department, dates = date_list, already_booked = already_booked, error = error)

    already_booked_department = (Appointments.query.join(User, Appointments.doctor_id == User.user_id).filter(Appointments.patient_id == patient_id, User.doctor_specialization == department_id, Appointments.status == "Booked").first())

    if already_booked_department:
        error = "You Already have an Appointment in this Department. You can Book Appointment in this Department once you Complete that Appointment."
        user_id = session.get("user_id")
        appointments = Appointments.query.filter_by(patient_id = user_id, status = "Booked").all()
        doctors = User.query.filter_by(user_role = "doctor").all()
        patients = User.query.filter_by(user_role = "patient").all()
        departments = Department.query.all()
        return render_template("patient_dashboard.html",appointments = appointments, patients=patients, doctors=doctors, user_name = session.get("user_name"), user_id = session.get("user_id"), departments = departments, error = error)

    existing_appointment = Appointments.query.filter_by(doctor_id = doctor_id, date = date_selected, time = time_selected).first()

    if existing_appointment:
        error = "This Slot has Already been Booked by Someone "
        booked_appointments = Appointments.query.filter_by(doctor_id = doctor.user_id, status = "Booked").all()
        already_booked = set()

        for booked in booked_appointments:
            already_booked.add((booked.date, booked.time))
        return render_template("check_availability.html", doctor = doctor, department = department, slots = slots_of_date.get(date_selected, []), dates = date_list, already_booked = already_booked, error = error, date_selected = date_selected)
    
    new_appointment = Appointments(patient_id = patient_id, doctor_id = doctor_id, date = date_selected, time = time_selected, status = "Booked")

    db.session.add(new_appointment)
    db.session.commit()

    
    error = "Your Appointment has been Booked Successfully"
    user_id = session.get("user_id")
    appointments = Appointments.query.filter_by(patient_id = user_id, status = "Booked").all()    
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()
    return render_template("patient_dashboard.html",appointments = appointments, patients=patients, doctors=doctors, user_name = session.get("user_name"), user_id = session.get("user_id"), departments = departments, error = error)

@app.route("/patient_dashboard/appointment_cancel/", methods=["GET","POST"])
def Patient_Cancelled():
    appointment_id = request.form.get("appointment_id")
    appointment = Appointments.query.get(appointment_id)
    user_id = session.get("user_id")
    appointments = Appointments.query.filter_by(patient_id = user_id, status = "Booked").all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()

    treatment = Treatment(appointment_id = appointment.appointment_id, diagnosis = "Appointment cancelled by Patient", prescription = "Appointment cancelled by Patient", patient_id = appointment.patient_id, doctor_id = appointment.doctor_id, date = appointment.date)
    db.session.add(treatment)
    appointment.status = "Cancelled by Patient"

    db.session.commit()
    error = "Appointment Cancelled"
    return render_template("patient_dashboard.html", appointments = appointments, patients=patients, doctors=doctors, user_id = user_id, user_name = session.get("user_name"), departments = departments, error = error)






@app.route("/doctor_dashboard", methods = ["GET","POST"])
def Doctor_Dashboard():

    if "user_role" not in session or session["user_role"] != "doctor":
        error = "Login or Sign up to Access"
        return render_template("/index.html", error = error)
    user_id = session.get("user_id")
    today = datetime.today().strftime("%d-%m-%Y")
    patient_absent = Appointments.query.filter(Appointments.doctor_id == user_id, Appointments.status == "Booked").all()

    for appointment in patient_absent:
        date = datetime.strptime(appointment.date, "%d-%m-%Y").date()

        if date < datetime.now().date() and appointment.status == "Booked":
            appointment.status = "Patient Absent"
    
    db.session.commit()
    
    todays_appointments = Appointments.query.filter_by(doctor_id = user_id, date = today, status = "Booked").all()
    upcoming_appointments = Appointments.query.filter(Appointments.doctor_id == user_id, Appointments.date != today, Appointments.status == "Booked").all()
    appointments = Appointments.query.filter_by(doctor_id = user_id).all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()

   
    return render_template("doctor_dashboard.html", upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, appointments = appointments, patients=patients, doctors=doctors, user_id = user_id, user_name = session.get("user_name"), departments = departments)

@app.route("/doctor_dashboard/provide_availability", methods = ["GET","POST"])
def Provide_Availability():
    doctor = session.get("user_id")
    slots = ["9am - 10am","10am - 11am","11am - 12pm","3pm - 4pm","4pm - 5pm","5pm - 6pm","6pm - 7pm","7pm - 8pm","8pm - 9pm"]

    dates=[]
    today = datetime.today()
    for i in range(7):
        date = today + timedelta(days=i)
        dates.append(date.strftime("%d-%m-%Y"))

    saved_availability = Availability.query.filter_by(doctor_id = doctor, status = "Available")
    saved_slots = set()

    for slot in saved_availability:
        saved_slots.add((slot.date, slot.time))

    return render_template("provide_availability.html", dates = dates, slots = slots, saved_slots = saved_slots)

@app.route("/doctor_dashboard/save_availability", methods = ["GET","POST"])
def Save_Availability():
    error = None
    doctor = session.get("user_id")

    slots_available = request.form.to_dict(flat=False)

    Availability.query.filter_by(doctor_id = doctor, status = "Available").delete()

    for key, values in slots_available.items():
        if key.startswith("availability["):
            date = key.replace("availability[", "").replace("][]","")

            for time in values:
                if time.strip() == "":
                    continue

                new_available = Availability(doctor_id = doctor, date = date, time = time, status = "Available")
                db.session.add(new_available)
    
    db.session.commit()
    error = "Availability Provided Successfully"
    user_id = session.get("user_id")
    today = datetime.today().strftime("%d-%m-%Y")
    todays_appointments = Appointments.query.filter_by(doctor_id = user_id, date = today, status = "Booked").all()
    upcoming_appointments = Appointments.query.filter(Appointments.doctor_id == user_id, Appointments.date != today, Appointments.status == "Booked").all()
    appointments = Appointments.query.filter_by(doctor_id = user_id).all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()
    return render_template("doctor_dashboard.html", error = error, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, appointments = appointments, patients=patients, doctors=doctors, user_id = user_id, user_name = session.get("user_name"), departments = departments)


@app.route("/doctor_dashboard/appointment_view_history", methods=["GET","POST"])
def Doctor_View_History():
    patient_id = request.args.get("patient_id")
    treatments = Treatment.query.filter(Treatment.patient_id == patient_id, Treatment.prescription != "Appointment cancelled", Treatment.prescription != "Appointment cancelled by Patient" ).all()
    return render_template("doctor_view_history.html",treatments = treatments)

@app.route("/doctor_dashboard/appointment_update", methods=["GET","POST"])
def Update():
    appointment_id = request.form.get("appointment_id")
    appointment = Appointments.query.get(appointment_id)
    return render_template("update.html",appointment=appointment)

@app.route("/doctor_dashboard/appointment_completed", methods=["GET","POST"])
def Completed():
    error = None
    appointment_id = request.form.get("appointment_id")

    appointment = Appointments.query.get(appointment_id)

    diagnosis = request.form.get("diagnosis")
    prescription = request.form.get("prescription")
    user_id = session.get("user_id")

    appointments = Appointments.query.filter_by(doctor_id = user_id).all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()
    today = datetime.today().strftime("%d-%m-%Y")
    todays_appointments = Appointments.query.filter_by(doctor_id = user_id, date = today, status = "Booked").all()
    upcoming_appointments = Appointments.query.filter(Appointments.doctor_id == user_id, Appointments.date != today, Appointments.status == "Booked").all()

    treatment = Treatment(appointment_id = appointment.appointment_id, diagnosis = diagnosis, prescription = prescription, patient_id = appointment.patient_id, doctor_id = appointment.doctor_id, date = appointment.date)
    appointment.status = "Completed"
    db.session.add(treatment)
    error = "History Updated Successfully"
    db.session.commit()
    
    return render_template("doctor_dashboard.html", upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments,appointments = appointments, patients=patients, doctors=doctors, user_id = user_id, user_name = session.get("user_name"), departments = departments, error = error)

@app.route("/doctor_dashboard/appointment_cancelled", methods=["GET","POST"])
def Doctor_Cancelled():
    appointment_id = request.form.get("appointment_id")
    appointment = Appointments.query.get(appointment_id)
    user_id = session.get("user_id")
    appointments = Appointments.query.filter_by(doctor_id = user_id).all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()

    today = datetime.today().strftime("%d-%m-%Y")
    todays_appointments = Appointments.query.filter_by(doctor_id = user_id, date = today, status = "Booked").all()
    upcoming_appointments = Appointments.query.filter(Appointments.doctor_id == user_id, Appointments.date != today, Appointments.status == "Booked").all()
    
    treatment = Treatment(appointment_id = appointment.appointment_id, diagnosis = "Appointment cancelled", prescription = "Appointment cancelled", patient_id = appointment.patient_id, doctor_id = appointment.doctor_id, date = appointment.date)
    db.session.add(treatment)
    appointment.status = "Cancelled by Doctor"

    db.session.commit()
    error = "Appointment Cancelled"
    return render_template("doctor_dashboard.html", upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, appointments = appointments, patients=patients, doctors=doctors, user_id = user_id, user_name = session.get("user_name"), departments = departments, error = error)






@app.route("/admin_dashboard", methods = ["GET","POST"])
def Admin_Dashboard():
    if "user_role" not in session or session["user_role"] != "admin":
        error = "Login or Sign up to Access"
        return render_template("/index.html", error = error)
    
    today = datetime.today().strftime("%d-%m-%Y")
    todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
    upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
    previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()
    return render_template("admin_dashboard.html",previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments )

@app.route("/admin_dashboard/search", methods = ["GET","POST"])
def Search():
    searched = request.args.get("search","").strip()
    if searched == "":
        return redirect("/admin_dashboard")
    
    id = searched.isdigit()

    searched_doctors = User.query.filter(User.user_role == "doctor",((User.user_name.ilike(f"{searched}%")) | ((User.user_id == int(searched)) if id else False))).all()
    searched_patients = User.query.filter(User.user_role == "patient",((User.user_name.ilike(f"{searched}%")) | ((User.user_id == int(searched)) if id else False))).all()
    searched_departments = Department.query.filter((Department.department_name.ilike(f"{searched}%")) | ((Department.department_id == int(searched)) if id else False)).all()
    today = datetime.today().strftime("%d-%m-%Y")
    todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
    upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
    previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
    
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()

    return render_template("admin_dashboard.html",previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, searched = searched, searched_doctors = searched_doctors, searched_patients = searched_patients, searched_departments = searched_departments, doctors = doctors, patients = patients, departments = departments)

@app.route("/admin_dashboard/all_doctors", methods = ["GET","POST"])
def All_Doctors():
    doctors = User.query.filter_by(user_role = "doctor").all()
    return render_template("all_doctors.html", doctors = doctors)


@app.route("/admin_dashboard/create", methods = ["GET","POST"])
def Create():
    departments = Department.query.all()
    return render_template("create.html", departments = departments)

@app.route("/admin_dashboard/create/add", methods = ["GET","POST"])
def Add_Doctor():
    if request.method == "POST":
        doctor_name = request.form["doctor_name"]
        department_id = request.form["specialization"]
        doctor_email = request.form["doctor_email"]
        doctor_password = request.form["doctor_password"]

        departments = Department.query.all()
        existing_department = Department.query.filter_by(department_id = department_id).first()
        existing_doctor = User.query.filter_by(user_email = doctor_email).first()
        if existing_doctor:
            error = "Doctor Already Exists" 
            return render_template("create.html", error = error, departments = departments)
        
        if existing_department:
            new_doctor = User(user_name = doctor_name,user_email = doctor_email, doctor_specialization = existing_department.department_id, user_password = doctor_password, user_role = "doctor")
            db.session.add(new_doctor)
            db.session.commit()
            today = datetime.today().strftime("%d-%m-%Y")
            todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
            upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
            previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
            doctors = User.query.filter_by(user_role = "doctor").all()
            patients = User.query.filter_by(user_role = "patient").all()
            departments = Department.query.all()
            return render_template("admin_dashboard.html",previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments )
        else:
            error = "Department does not Exist"
            return render_template("create.html", error = error, departments = departments)


@app.route("/admin_dashboard/doctor/edit/<int:user_id>", methods = ["GET","POST"])
def Edit(user_id):
    doctor = User.query.get(user_id)
    departments = Department.query.all()
    return render_template("edit_doctor.html",doctor=doctor,departments=departments)

@app.route("/admin_dashboard/doctor/edit/edit_doctor/<int:user_id>", methods = ["GET","POST"])
def Edit_Doctor(user_id):
    error = None
    doctor = User.query.get(user_id)
    departments = Department.query.all()
    if request.method == "POST":
        doctor.user_name = request.form["doctor_name"]
        doctor.doctor_specialization = request.form["specialization"]
        doctor.user_email = request.form["doctor_email"]
        doctor.user_password = request.form["doctor_password"]
        existing_user = User.query.filter(User.user_email == request.form["doctor_email"], User.user_id != user_id).first()
        if existing_user:
            error = "Email Already Exist"
            return render_template("edit_doctor.html",doctor=doctor,departments=departments, error = error)
        
        db.session.commit()
        today = datetime.today().strftime("%d-%m-%Y")
        todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
        upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
        previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
        doctors = User.query.filter_by(user_role = "doctor").all()
        patients = User.query.filter_by(user_role = "patient").all()
        departments = Department.query.all()
        return render_template("admin_dashboard.html",previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments )
            
@app.route("/admin_dashboard/doctor/all_edit/<int:user_id>", methods = ["GET","POST"])
def All_Edit(user_id):
    doctor = User.query.get(user_id)
    departments = Department.query.all()
    return render_template("edit_all_doctors.html",doctor=doctor,departments=departments)


@app.route("/admin_dashboard/doctor/edit/edit_all_doctor/<int:user_id>", methods = ["GET","POST"])
def Edit_All_Doctor(user_id):
    error = None
    departments = Department.query.all()
    doctor = User.query.get(user_id)
    if request.method == "POST":
        doctor.user_name = request.form["doctor_name"]
        doctor.doctor_specialization = request.form["specialization"]
        doctor.user_email = request.form["doctor_email"]
        doctor.user_password = request.form["doctor_password"]
        existing_user = User.query.filter(User.user_email == request.form["doctor_email"], User.user_id != user_id).first()
        if existing_user:
            error = "Email Already Exist"
            return render_template("edit_doctor.html",doctor=doctor,departments=departments, error = error)
        
        db.session.commit()
        return redirect("/admin_dashboard/all_doctors")

@app.route("/admin_dashboard/doctor/blacklist/<int:user_id>", methods = ["GET","POST"])
def Doctor_Blacklist(user_id):
    user = User.query.get(user_id)

    if user.blacklist:
        user.blacklist = False
    else:
        user.blacklist = True

    db.session.commit()
    today = datetime.today().strftime("%d-%m-%Y")
    todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
    upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
    previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()
    return render_template("admin_dashboard.html", previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments )
        
@app.route("/admin_dashboard/doctor/blacklist/all_doctors/<int:user_id>", methods = ["GET","POST"])
def All_Doctors_Blacklist(user_id):
    user = User.query.get(user_id)

    if user.blacklist:
        user.blacklist = False
    else:
        user.blacklist = True

    db.session.commit()
    return redirect("/admin_dashboard/all_doctors")

@app.route("/admin_dashboard/doctor/delete/<int:user_id>", methods = ["GET","POST"])
def Doctor_Delete(user_id):
    error = None
    appointments = Appointments.query.filter_by(doctor_id = user_id).first()
    if appointments:
        error = "Cannot Delete Doctor. Doctor has Appointments"
        doctors = User.query.filter_by(user_role = "doctor").all()
        return render_template("admin_dashboard.html", previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments, error = error )
    
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    today = datetime.today().strftime("%d-%m-%Y")
    todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
    upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
    previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()
    return render_template("admin_dashboard.html", previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments )
    
@app.route("/admin_dashboard/doctor/delete/all_doctors/<int:user_id>", methods = ["GET","POST"])
def All_Doctor_Delete(user_id):
    appointments = Appointments.query.filter_by(doctor_id = user_id).first()
    error = None
    if appointments:
        error = "Cannot Delete Doctor. Doctor has Appointments"
        doctors = User.query.filter_by(user_role = "doctor").all()
        return render_template("all_doctors.html", doctors = doctors, error = error)
        
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    doctors = User.query.filter_by(user_role = "doctor").all()
    return render_template("all_doctors.html", doctors = doctors, error = error)


@app.route("/admin_dashboard/all_patients", methods = ["GET","POST"])
def All_Patients():
    patients = User.query.filter_by(user_role = "patient").all()
    return render_template("all_patients.html", patients = patients)

@app.route("/admin_dashboard/patient/blacklist/<int:user_id>", methods = ["GET","POST"])
def Patient_Blacklist(user_id):
    user = User.query.get(user_id)

    if user.blacklist:
        user.blacklist = False
    else:
        user.blacklist = True

    db.session.commit()

    today = datetime.today().strftime("%d-%m-%Y")
    todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
    upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
    previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()
    return render_template("admin_dashboard.html", previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments )

@app.route("/admin_dashboard/patient/blacklist/all_patients/<int:user_id>", methods = ["GET","POST"])
def All_Patient_Blacklist(user_id):
    user = User.query.get(user_id)

    if user.blacklist:
        user.blacklist = False
    else:
        user.blacklist = True

    db.session.commit()

    return redirect("/admin_dashboard/all_patients")

@app.route("/admin_dashboard/patient/delete/<int:user_id>", methods = ["GET","POST"])
def Patient_Delete(user_id):
    user = User.query.get(user_id)
    error = None
    appointments = Appointments.query.filter_by(patient_id = user_id).first()
    if appointments:
        error = "Cannot Delete Patient. Patient has Appointments"
        patients = User.query.filter_by(user_role = "patient").all()
        today = datetime.today().strftime("%d-%m-%Y")
        todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
        upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
        previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
        doctors = User.query.filter_by(user_role = "doctor").all()
        departments = Department.query.all()
        return render_template("admin_dashboard.html", previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments, error = error )
    
    db.session.delete(user)
    db.session.commit()
    today = datetime.today().strftime("%d-%m-%Y")
    todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
    upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
    previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()
    departments = Department.query.all()
    return render_template("admin_dashboard.html", previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments )
    
@app.route("/admin_dashboard/patient/delete/all_patients/<int:user_id>", methods = ["GET","POST"])
def All_Patient_Delete(user_id):
    user = User.query.get(user_id)
    error = None
    appointments = Appointments.query.filter_by(patient_id = user_id).first()
    if appointments:
        error = "Cannot Delete Patient. Patient has Appointments"
        patients = User.query.filter_by(user_role = "patient").all()
        return render_template("all_patients.html",patients = patients, error = error )
    
    db.session.delete(user)
    db.session.commit()
    return redirect("/admin_dashboard/all_patients")

@app.route("/admin_dashboard/create_department", methods = ["GET","POST"])
def Create_Department():
    return render_template("create_department.html")

@app.route("/admin_dashboard/create_department/add", methods = ["GET","POST"])
def Add_Department():
    if request.method == "POST":
        department_name = request.form["department_name"]
        description = request.form["description"]
        

        existing_department = Department.query.filter_by(department_name = department_name).first()
        if existing_department:
            error = "Department Already Exists" 
            return render_template("create_department.html", error = error)
        new_department = Department(department_name = department_name, description = description)

        db.session.add(new_department)
        db.session.commit()
        today = datetime.today().strftime("%d-%m-%Y")
        todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
        upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
        previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
        doctors = User.query.filter_by(user_role = "doctor").all()
        patients = User.query.filter_by(user_role = "patient").all()
        departments = Department.query.all()
        return render_template("admin_dashboard.html", previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments )
            
@app.route("/admin_dashboard/department/delete/<int:department_id>", methods = ["POST"])
def Department_Delete(department_id):
    error = None
    doctors_present = User.query.filter_by(doctor_specialization = department_id).all()
    department = Department.query.get(department_id)
    doctors = User.query.filter_by(user_role = "doctor").all()
    patients = User.query.filter_by(user_role = "patient").all()

    if department is None:
        return render_template("admin_dashboard.html", doctors = doctors, patients = patients, departments = departments, error = error )
    if doctors_present:
        error = "Cannot delete department. There are Doctors Present in the Department"
        departments = Department.query.all()
        return render_template("admin_dashboard.html", doctors = doctors, patients = patients, departments = departments, error = error )
    else:
        db.session.delete(department)
        db.session.commit()
        departments = Department.query.all()
        today = datetime.today().strftime("%d-%m-%Y")
        todays_appointments = Appointments.query.filter_by( date = today, status = "Booked").all()
        upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
        previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
        return render_template("admin_dashboard.html",error = error, previous_appointments = previous_appointments, upcoming_appointments = upcoming_appointments, todays_appointments = todays_appointments, doctors = doctors, patients = patients, departments = departments )
        

@app.route("/admin_dashboard/department/delete/all_departments/<int:department_id>", methods = ["POST"])
def All_Department_Delete(department_id):
    error = None
    doctors_present = User.query.filter_by(doctor_specialization = department_id).all()
    department = Department.query.get(department_id)
    department = Department.query.get(department_id)

    if department is None:
        return render_template("all_departments.html", departments = departments, error = error )
    if doctors_present:
        error = "Cannot delete department. There are Doctors Present in the Department"
        departments = Department.query.all()
        return render_template("all_departments.html", departments = departments,error = error)
    else:
        db.session.delete(department)
        db.session.commit()
        departments = Department.query.all()
        return render_template("all_departments.html", departments = departments,error = error)

    
@app.route("/admin_dashboard/registered_doctor/<int:dept_id>", methods = ["GET","POST"])
def Registered_Doctors(dept_id):
    doctors = User.query.filter_by(user_role = "doctor", doctor_specialization = dept_id).all()
    department = Department.query.get(dept_id)
    return render_template("registered_doctor.html", doctors=doctors,department=department)

@app.route("/admin_dashboard/all_departments", methods = ["GET","POST"])
def All_Departments():
    departments = Department.query.all()
    return render_template("all_departments.html", departments = departments)

@app.route("/admin_dashboard/history", methods=["GET","POST"])
def Admin_View_History():
    patient_id = request.args.get("patient_id")
    treatments = Treatment.query.filter(Treatment.patient_id == patient_id, Treatment.prescription != "Appointment cancelled", Treatment.prescription != "Appointment cancelled by Patient" ).all()
    return render_template("admin_view_history.html",treatments = treatments)

@app.route("/admin_dashboard/previous_appointments", methods = ["GET","POST"])
def Previous_Appointments():
    previous_appointments = Appointments.query.filter(Appointments.status != "Booked" ).all()
    return render_template("previous_appointments.html", previous_appointments = previous_appointments)

@app.route("/admin_dashboard/upcoming_appointments", methods = ["GET","POST"])
def Upcoming_Appointments():
    today = datetime.today().strftime("%d-%m-%Y")
    upcoming_appointments = Appointments.query.filter(Appointments.date != today, Appointments.status == "Booked" ).all()
    return render_template("upcoming_appointments.html", upcoming_appointments = upcoming_appointments)






if __name__ == "__main__":
    db.create_all()
    if not User.query.filter_by(user_role = "admin").first():
        admin = User(user_name = "Admin", user_email = "admin@gmail.com", user_password = "admin", user_role = "admin")
        db.session.add(admin)
        db.session.commit()

    app.run(debug = True)
    