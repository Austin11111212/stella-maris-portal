
# =========================================
# STELLA MARIS COLLEGE PORTAL SYSTEM
# FULL UPDATED VERSION
# =========================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort


)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from functools import wraps
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId
from io import BytesIO
from flask import make_response, render_template
from xhtml2pdf import pisa
from datetime import datetime
from flask import jsonify
import qrcode
import base64
from io import BytesIO
import os
import uuid
import random

# =========================================
# LOAD ENV
# =========================================
load_dotenv()

# =========================================
# FLASK APP
# =========================================
app = Flask(__name__)


app.secret_key = os.environ.get(
    "SECRET_KEY",
    "stella_maris_secret_key_2026"
)

@app.template_filter("format_date")
def format_date(value):
    if not value:
        return "-"

    try:
        dt = datetime.strptime(value, "%Y-%m-%d")

        day = dt.day
        if 10 <= day % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

        return f"{day}{suffix} {dt.strftime('%B, %Y')}"
    except Exception:
        return value
def save_activity(action, student_id="", session="", term="", admin="Administrator"):

    activity_logs_collection.insert_one({

        "action": action,

        "student_id": student_id,

        "session": session,

        "term": term,

        "admin": admin,

        "date": datetime.now().strftime("%d %B %Y"),

        "time": datetime.now().strftime("%I:%M %p")

    })

# =========================================
# UPLOAD FOLDER
# =========================================
UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================================
# MONGODB CONNECTION
# =========================================
MONGO_URI = os.getenv("MONGO_URI")

students_collection = None
admins_collection = None
classes_collection = None
teachers_collection = None
settings_collection = None
parents_collection = None
attendance_collection = None
term = None
session_year = None

try:

    if MONGO_URI:

        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=10000
        )

        client.admin.command("ping")

        db = client["school_portal"]
        students_collection = db["students"]
        admins_collection = db["admins"]
        classes_collection = db["classes"]
        results_collection = db["results"]
        teachers_collection = db["teachers"]
        parents_collection = db["parents"]
        attendance_collection = db["attendance"]
        student_checkin_collection = db["student_checkin"]
        settings_collection = db["settings"]
        activity_logs_collection = db["activity_logs"]
        print("✅ MongoDB Connected Successfully")

    else:

        print("⚠️ MONGO_URI not found")

except Exception as e:

    print("❌ MongoDB Connection Failed")
    print(e)

# =========================================
# SCHOOL INFO
# =========================================
SCHOOL_INFO = {

    "name": "Stella Maris College",

    "address": "No. 21 Awoyokun Street, Onipanu, Lagos | 2 Bode Thomas Road, Palmgrove, Lagos",

    "phone": "+2348060507286",
    "email": "info@stellamariscollege.com",

    "website": "https://stella-maris-portal.onrender.com",

    "motto": "Knowledge • Discipline • Excellence",

    "principal": "mr Ransome Aremo",

    "current_term": "Third Term",

    "current_session": "2025/2026",

    "logo": "images/logo.png",
    "stamp": "images/school_stamp.png",
    "school_closed": "28th August 2026",
    "next_term_begins": "08 September 2026",

}

# =========================================
# SUBJECTS
# =========================================
SUBJECTS = [

    "Mathematics",
    "English Language",
    "Biology",
    "Economics",
    "Government",
    "Marketing",
    "Literature",
    "Digital Technology",
    "C.R.S",
    "C.C.A",
    "Home Economics",
    "Social Studies",
    "French",
    "Yoruba",
    "Physical and Health Education",
    "Music",
    "Business Studies",
    "Agricultural Science",
    "Intermediate Science",
    "Commerce",
    "Technical Drawing",
    "Accounting",
    "Further Mathematics",
    "Chemistry",
    "Physics",
    "Citizenship Education"
]

# =========================================
# CLASSES
# =========================================
CLASSES = {

    "JSS1": "JSS1",
    "JSS2": "JSS2",
    "JSS3": "JSS3",
    "SS1": "SS1",
    "SS2": "SS2",
    "SS3": "SS3"
}

# =========================================
# LOGIN REQUIRED
# =========================================
def admin_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if not session.get("admin"):

            return redirect(
                url_for("admin_login")
            )

        return f(*args, **kwargs)

    return wrapper


def student_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if not session.get("student"):

            return redirect(
                url_for("student_login")
            )

        return f(*args, **kwargs)

    return wrapper


def login_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if not session.get("student"):

            return redirect(
                url_for("student_login")
            )

        return f(*args, **kwargs)

    return wrapper

def recalculate_positions(session, term, student_class):

    # Get all published or existing results for this class
    results = list(results_collection.find({
        "session": session,
        "term": term,
        "class": student_class
    }))

    # Sort by average_score (highest first)
    results.sort(
        key=lambda r: r.get("average_score", 0),
        reverse=True
    )

    position = 1

    for result in results:

        results_collection.update_one(

            {
                "_id": result["_id"]
            },

            {
                "$set": {
                    "position": position
                }
            }
        )

        position += 1
def ordinal(n):

    if 10 <= n % 100 <= 20:
        suffix = "th"

    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd"
        }.get(n % 10, "th")

    return f"{n}{suffix}"

# =========================================
# GRADE SYSTEM
# =========================================
def calculate_grade(score):

    try:
        score = float(score)

    except:
        score = 0

    if score >= 75:
        return "A1", "Excellent"

    elif score >= 70:
        return "B2", "Very Good"

    elif score >= 65:
        return "B3", "Good"

    elif score >= 60:
        return "C4", "Credit"

    elif score >= 55:
        return "C5", "LowCredit"

    elif score >= 50:
        return "C6", "Pass"

    elif score >= 45:
        return "D7", "Fair"

    elif score >= 40:
        return "E8", "Weak"

    else:
        return "F9", "Fail"

# =========================================
# GET SCHOOL SETTINGS
# =========================================
def get_school_settings():

    settings = settings_collection.find_one({"type": "school_settings"})

    if not settings:

        settings = {

            "type": "school_settings",

            "current_session": "2025/2026",

            "current_term": "Third Term",
            "school_type": "Day School",
            "result_approval": "Yes",

"student_login": "Enabled",

"parent_login": "Enabled",

"teacher_login": "Enabled",

"maximum_subjects": 20,

"portal_notice": ""

        }

        settings_collection.insert_one(settings)

    return settings

# ==========================================================
# CALCULATE STUDENT RESULT
# ==========================================================
# ==========================================================
# CALCULATE STUDENT RESULT
# ==========================================================
def calculate_result(student):

    if not student:
        return student

    results = student.get("results", {})

    total_score = 0
    total_subjects = 0

    passed_subjects = 0
    failed_subjects = 0

    highest_score = 0
    lowest_score = 100

    highest_subject = "-"
    lowest_subject = "-"
    best_grade = "-"

    for subject, data in results.items():

        test = int(data.get("test", 0) or 0)
        exam = int(data.get("exam", 0) or 0)

        total = test + exam

        grade, remark = calculate_grade(total)

        data["test"] = test
        data["exam"] = exam
        data["total"] = total
        data["grade"] = grade
        data["remark"] = remark

        total_score += total
        total_subjects += 1

        if total >= 50:
            passed_subjects += 1
        else:
            failed_subjects += 1

        if total > highest_score:
            highest_score = total
            highest_subject = subject
            best_grade = grade

        if total < lowest_score:
            lowest_score = total
            lowest_subject = subject

    # ---------------------------------------
    # Average
    # ---------------------------------------

    if total_subjects:

        calculated_average = round(
            total_score / total_subjects,
            2
        )

    else:

        calculated_average = 0
        lowest_score = 0

    # ---------------------------------------
    # Use database values if they already exist
    # ---------------------------------------

    result_doc = student.get("result", {})

    average_score = result_doc.get(
        "average_score",
        calculated_average
    )

    grade = result_doc.get(
        "grade",
        calculate_grade(average_score)[0]
    )

    remark = result_doc.get(
        "remark",
        calculate_grade(average_score)[1]
    )

    percentage = result_doc.get(
        "percentage",
        average_score
    )

    performance = result_doc.get(
        "performance",
        remark
    )

    progress_color = "#1565c0"

    if average_score >= 75:
        progress_color = "#2e7d32"

    elif average_score >= 65:
        progress_color = "#1565c0"

    elif average_score >= 50:
        progress_color = "#ef6c00"

    elif average_score >= 40:
        progress_color = "#fb8c00"

    else:
        progress_color = "#c62828"

    promotion_status = result_doc.get(
        "promotion_status",
        "PROMOTED" if average_score >= 50 else "NOT PROMOTED"
    )

    attendance = student.get("attendance", {})

    opened = attendance.get("opened", 0)
    present = attendance.get("present", 0)

    if opened:

        attendance_percentage = round(
            (present / opened) * 100,
            2
        )

    else:

        attendance_percentage = 0

    # ---------------------------------------
    # Save back
    # ---------------------------------------

    student["results"] = results

    student["total"] = total_score

    student["average_score"] = average_score
    student["percentage"] = percentage

    student["grade"] = grade
    student["remark"] = remark

    student["performance"] = performance
    student["progress_color"] = progress_color

    student["total_subjects"] = total_subjects
    student["passed_subjects"] = passed_subjects
    student["failed_subjects"] = failed_subjects

    student["highest_score"] = highest_score
    student["lowest_score"] = lowest_score

    student["highest_subject"] = highest_subject
    student["lowest_subject"] = lowest_subject

    student["highest_mark"] = highest_score
    student["lowest_mark"] = lowest_score

    student["best_grade"] = best_grade

    student["attendance_percentage"] = attendance_percentage
    student["promotion_status"] = promotion_status

    return student


def calculate_cumulative_result(student_id, session_year):
    """
    Calculate simple cumulative result for a student for a given session.
    Returns a dict with total_score, average_score and terms_count.
    """
    try:
        results = list(results_collection.find({
            "student_id": str(student_id),
            "session": session_year,
            "published": True
        }))
    except Exception:
        return {"total_score": 0, "average_score": 0, "terms_count": 0}

    if not results:
        return {"total_score": 0, "average_score": 0, "terms_count": 0}

    total_score = 0
    count = 0

    for r in results:
        total = r.get("total_score") or r.get("total") or 0
        try:
            total = float(total)
        except Exception:
            total = 0
        total_score += total
        count += 1

    average = round(total_score / count, 2) if count else 0

    return {"total_score": total_score, "average_score": average, "terms_count": count}

# =========================================
# HOME
# =========================================
@app.route("/")
def home():

    if session.get("admin"):
        return redirect(url_for("dashboard"))

    if session.get("student"):
        return redirect(url_for("student_dashboard"))

    return redirect(url_for("student_login"))


# =========================================
# STUDENT LOGIN
# =========================================
@app.route(
    "/login",
    methods=["GET", "POST"]
)
def student_login():

    if request.method == "POST":

        student_id = request.form.get(
            "student_id"
        )

        password = request.form.get(
            "password"
        )

        student = students_collection.find_one({

            "student_id": student_id

        })

        if student and check_password_hash(
            student["password"],
            password
        ):

            session["student"] = student_id

            return redirect(
                url_for("student_dashboard")
            )

        flash("Invalid Login Details")

    return render_template(

        "login.html",

        school_name=SCHOOL_INFO["name"],

        school_logo=SCHOOL_INFO["logo"]
    )


# =========================================
# ADMIN LOGIN
# =========================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":

            session["admin"] = True

            return redirect(
                url_for("dashboard")
            )

        flash("Invalid Admin Login")

    return render_template(
        "admin_login.html"
    )

# =========================================
# ADMIN DASHBOARD
# =========================================
@app.route("/admin/dashboard")
@admin_required
def dashboard():

    flash("Dashboard loaded successfully!", "success")

    if students_collection is not None:
        students = list(students_collection.find())
    else:
        students = []

    total_students = len(students)

    total_results = 0

    class_counts = {}

    grade_counts = {
        "A": 0,
        "B": 0,
        "C": 0,
        "F": 0
    }
    for student in students:

        student.pop("_id", None)

        calculate_result(student)

        # Count Classes
        class_name = student.get("class", "Unknown")

        class_counts[class_name] = (
            class_counts.get(class_name, 0) + 1
        )

        # Count Results
        if student.get("results"):
            total_results += 1

        # Count Grades
        grade = str(student.get("grade", ""))

        if grade.startswith("A"):
            grade_counts["A"] += 1

        elif grade.startswith("B"):
            grade_counts["B"] += 1

        elif grade.startswith("C"):
            grade_counts["C"] += 1

        else:
            grade_counts["F"] += 1

    # =====================================
    # TEACHERS
    # =====================================

    total_teachers = 0

    try:
        total_teachers = teachers_collection.count_documents({})
    except:
        pass

    # =====================================
    # ATTENDANCE
    # =====================================

    today_attendance = 0
    absent_today = 0

    try:

        today_attendance = attendance_collection.count_documents(
            {"status": "Present"}
        )

        absent_today = attendance_collection.count_documents(
            {"status": "Absent"}
        )

    except:
        pass

    attendance_rate = 100

    # =====================================
    # SCHOOL SETTINGS
    # =====================================

    school = get_school_settings()

    # =====================================
    # ACADEMIC SESSIONS
    # =====================================

    sessions = [
        "2023/2024",
        "2024/2025",
        "2025/2026",
        "2026/2027"
    ]

    return render_template(

        "dashboard.html",

        students=students,

        school=school,

        sessions=sessions,

        school_name=school.get("name"),

        school_logo=school.get("logo"),

        current_term=school.get("current_term"),

        current_session=school.get("current_session"),

        total_students=total_students,

        total_results=total_results,

        class_counts=class_counts,

        attendance_rate=attendance_rate,

        grade_counts=grade_counts,

        total_teachers=total_teachers,

        today_attendance=today_attendance,

        absent_today=absent_today

    )
@app.route("/admin/student_profile/<student_id>")
@admin_required
def student_profile_admin(student_id):

    print("=" * 50)
    print("PROFILE PAGE REQUESTED")
    print("STUDENT ID FROM URL:", student_id)
    print("=" * 50)

    if students_collection is None:
        flash("Database connection error", "danger")
        return redirect(url_for("dashboard"))

    student = students_collection.find_one({
        "student_id": str(student_id).strip()
    })

    print("DATABASE RESULT:", student)

    if student is None:

        all_students = list(
            students_collection.find(
                {},
                {"student_id": 1, "name": 1}
            )
        )

        print("AVAILABLE STUDENTS:")
        for s in all_students:
            print(
                s.get("student_id"),
                "-",
                s.get("name")
            )

        flash(
            f"Student not found: {student_id}",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    student.pop("_id", None)

    calculate_result(student)

    return render_template(
        "student_profile_admin.html",
        student=student,
        school_name=SCHOOL_INFO["name"],
        school_logo=SCHOOL_INFO["logo"],
        current_term=SCHOOL_INFO["current_term"],
        current_session=SCHOOL_INFO["current_session"]
    )

# =========================================
# ADD STUDENT
# =========================================
@app.route(
    "/admin/add_student",
    methods=["GET", "POST"]
)
@admin_required
def add_student():

    if request.method == "POST":

        name = request.form.get("name")
        registration_number = request.form.get("registration_number")
        club = request.form.get("club")

        password = request.form.get(
            "password"
        )

        gender = request.form.get(
            "gender"
        )

        class_name = request.form.get(
            "class"
        )

        dob = request.form.get("dob")

        parent_phone = request.form.get(
            "parent_phone"
        )
        parent_email = request.form.get(
    "parent_email"
)

        address = request.form.get(
            "address"
        )

        student_id = request.form.get(
            "student_id"
        )
        house = request.form.get("house")
        passport = request.files.get(
            "passport"
        )

        filename = "default.png"

        if passport and passport.filename:

            filename = secure_filename(
                passport.filename
            )

            passport.save(

                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )

            )

        if not student_id:

            student_id = str(
                uuid.uuid4()
            )[:8].upper()

        selected_subjects = request.form.getlist(
            "subjects"
        )

        if not selected_subjects:

            selected_subjects = SUBJECTS

        results = {}

        for subject in selected_subjects:

            results[subject] = {

                "test": 0,
                "exam": 0
            }

        student = {

            # ==========================
            # BASIC DETAILS
            # ==========================

            "student_id": student_id,

            "full_name": name,

            "password": generate_password_hash(password),

            "gender": gender,

            "class": class_name,
            "registration_number": registration_number,
            "club": club,


            "arm": request.form.get("arm"),

            "roll_number": request.form.get("roll_number"),

            "status": "Active",

            # ==========================
            # PERSONAL INFORMATION
            # ==========================

            "date_of_birth": dob,

            "state": request.form.get("state"),

            "nationality": request.form.get("nationality"),

            "religion": request.form.get("religion"),

            "blood_group": request.form.get("blood_group"),

            "genotype": request.form.get("genotype"),

            "house": request.form.get("house"),

            "address": address,

            # ==========================
            # PARENT INFORMATION
            # ==========================

            "father_name": request.form.get("father_name"),

            "mother_name": request.form.get("mother_name"),

            "guardian_name": request.form.get("guardian_name"),

            "guardian_relationship": request.form.get("guardian_relationship"),

            "father_phone": request.form.get("father_phone"),

            "mother_phone": request.form.get("mother_phone"),

            "guardian_phone": request.form.get("guardian_phone"),

            "parent_phone": parent_phone,

            "parent_email": parent_email,

            "father_occupation": request.form.get("father_occupation"),

            "mother_occupation": request.form.get("mother_occupation"),

            "emergency_contact": request.form.get("emergency_contact"),

            "emergency_relationship": request.form.get("emergency_relationship"),

            "parent_address": request.form.get("parent_address"),

            # ==========================
            # ACADEMIC INFORMATION
            # ==========================

            "admission_date": request.form.get("admission_date"),

            "session": SCHOOL_INFO["current_session"],

            "term": SCHOOL_INFO["current_term"],

            # ==========================
            # PASSPORT
            # ==========================

            "passport": filename,

            # ==========================
            # RESULTS
            # ==========================

            "results": results,

            # ==========================
            # ATTENDANCE
            # ==========================

            "attendance": {

                "opened": 100,

                "present": 95,

                "absent": 5

            },
# ==========================
# AFFECTIVE DOMAIN
# ==========================

"affective": {

    "punctuality": 0,
    "attendance": 0,
    "neatness": 0,
    "honesty": 0,
    "politeness": 0,
    "leadership": 0,
    "obedience": 0,
    "relationship": 0,
    "cooperation": 0,
    "self_control": 0

},

# ==========================
# PSYCHOMOTOR DOMAIN
# ==========================

"psychomotor": {

    "handwriting": 0,
    "sports": 0,
    "drawing": 0,
    "craft": 0,
    "music": 0,
    "creativity": 0,
    "communication": 0,
    "practical_work": 0,
    "computer_skills": 0,
    "team_work": 0

},

            # ==========================
            # SUMMARY
            # ==========================

            "position": "-",

            "grade": "F9",

            "remark": "",

            "average_score": 0,

            "total": 0,

            "performance": "-",

            "promotion_status": "PROMOTED",

            # ==========================
            # STAFF
            # ==========================

            "form_teacher": "Mrs Johnson",

            "principal": SCHOOL_INFO["principal"],

            "next_term_begins": "September 10, 2026"

        }
        calculate_result(student)
        students_collection.insert_one(
            student
            )
        flash(
            "Student Added Successfully"
            )
        return redirect(
                    url_for("dashboard")
                )

    return render_template(

        "add_student.html",

        school_name=SCHOOL_INFO["name"],

        school_logo=SCHOOL_INFO["logo"],

        SCHOOL_INFO=SCHOOL_INFO,

        current_session=SCHOOL_INFO["current_session"],

        current_term=SCHOOL_INFO["current_term"],

        classes=CLASSES,

        subjects=SUBJECTS

        )
# ==========================================================
# EDIT STUDENT RESULT
# ==========================================================
@app.route("/admin/edit_results/<student_id>", methods=["GET"])
@admin_required
def edit_results(student_id):

    # ==========================================
    # GET STUDENT
    # ==========================================

    student = students_collection.find_one({
        "student_id": student_id
    })

    if not student:

        flash("Student not found.", "danger")

        return redirect(
            url_for("dashboard")
        )

    # ==========================================
    # LOAD SCHOOL SETTINGS
    # ==========================================

    settings = get_school_settings()

    current_session = settings.get(
        "current_session",
        "2025/2026"
    )

    current_term = settings.get(
        "current_term",
        "Third Term"
    )
    # ==========================================
    # PHASE 2
    # GET SELECTED SESSION & TERM
    # ==========================================

    selected_session = request.args.get(

        "session",

        current_session

    )

    selected_term = request.args.get(

        "term",

        current_term

    )
    # ==========================================
    # PHASE 3
    # LOAD THE SELECTED RESULT
    # ==========================================

    existing_result = results_collection.find_one({

        "student_id": student_id,

        "session": selected_session,

        "term": selected_term

    })

    if existing_result:

        results = existing_result.get(
            "results",
            {}
        )

        attendance = existing_result.get(
            "attendance",
            {}
        )

        affective = existing_result.get(
            "affective",
            {}
        )

        psychomotor = existing_result.get(
            "psychomotor",
            {}
        )

    else:

        results = {}

        attendance = {}

        affective = {}

        psychomotor = {}
    # ==========================================
    # PHASE 4
    # LOAD ALL AVAILABLE RESULTS
    # ==========================================

    student["all_results"] = list(

        results_collection.find({

            "student_id": student_id

        }).sort([

            ("session", -1),

            ("term", -1)

        ])

    )
        # =====================================
    # PHASE 19
    # CHECK IF RESULT IS LOCKED
    # =====================================

    if existing_result and existing_result.get("locked", False):

        flash(
            "This result has been locked and cannot be edited.",
            "danger"
        )

        return redirect(url_for("results"))

    # ==========================================
    # SUBJECT LIST
    # ==========================================

    subjects = list(results.keys())

    if not subjects:

        subjects = list(

            student.get("results", {}).keys()

        )
    # ==========================================
    # PHASE 5
    # RENDER EDIT RESULT PAGE
    # ==========================================

    return render_template(

        "edit_results.html",

        student=student,

        results=results,

        attendance=attendance,

        affective=affective,

        psychomotor=psychomotor,

        subjects=subjects,

        school=settings,

        school_name=settings.get("name"),

        school_logo=settings.get("logo"),

        current_session=selected_session,

        current_term=selected_term

    )
@app.route("/admin/edit_student/<student_id>", methods=["GET", "POST"])
@admin_required
def edit_student(student_id):

    student = students_collection.find_one({
        "student_id": student_id
    })

    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        update_data = {
            "full_name": request.form.get("full_name"),
            "class": request.form.get("class"),
            "gender": request.form.get("gender"),
            "house": request.form.get("house")
        }

        students_collection.update_one(
            {"student_id": student_id},
            {"$set": update_data}
        )

        flash("Student updated successfully.", "success")

        return redirect(url_for("edit_student", student_id=student_id))

    return render_template(
        "edit_student.html",
        student=student
    )
@app.route("/admin/delete_result/<student_id>", methods=["POST"])
@admin_required
def delete_result(student_id):

    # ============================================
    # SUPPORT BOTH FORM SUBMISSION & FETCH()
    # ============================================

    if request.is_json:

        data = request.get_json()

        session_name = data.get("session", "").strip()
        term = data.get("term", "").strip()

    else:

        session_name = request.form.get("session", "").strip()
        term = request.form.get("term", "").strip()

    print("=" * 60)
    print("DELETE RESULT")
    print("Student ID:", student_id)
    print("Session:", session_name)
    print("Term:", term)
    print("=" * 60)

    result = results_collection.find_one({

        "student_id": student_id,

        "session": {
            "$in": [
                session_name,
                f"{session_name} Academic Session"
            ]
        },

        "term": term

    })

    print("Found Result:", result)

    if not result:

        if request.is_json:

            return jsonify({
                "success": False,
                "message": "Result not found."
            })

        flash("Result not found.", "danger")
        return redirect(url_for("results"))

    # ============================================
    # DO NOT DELETE LOCKED RESULTS
    # ============================================

    if result.get("locked", False):

        if request.is_json:

            return jsonify({
                "success": False,
                "message": "Locked results cannot be deleted."
            })

        flash("Locked results cannot be deleted.", "danger")
        return redirect(url_for("results"))

    # ============================================
    # DELETE RESULT
    # ============================================

    results_collection.delete_one({

        "_id": result["_id"]

    })

    print("Result Deleted Successfully")

    if request.is_json:

        return jsonify({

            "success": True,

            "message": "Result deleted successfully."

        })

    flash("Result deleted successfully.", "success")

    return redirect(

        url_for(

            "results",

            session=session_name,

            term=term

        )

    )

    # =========================================
    # STUDENT DASHBOARD
    # =========================================
@app.route("/student/dashboard")
@student_required
def student_dashboard():

    # =====================================================
    # PHASE 1
    # LOAD SCHOOL SETTINGS
    # =====================================================

    school = get_school_settings()

    # =====================================================
    # GET LOGGED-IN STUDENT
    # =====================================================

    student_id = session.get("student")

    if not student_id:
        session.clear()
        flash("Please login again.", "warning")
        return redirect(url_for("student_login"))

    # =====================================================
    # LOAD STUDENT RECORD
    # =====================================================

    student = students_collection.find_one({
        "student_id": student_id
    })

    if not student:
        session.clear()
        flash("Student account not found.", "danger")
        return redirect(url_for("student_login"))

    student.pop("_id", None)

    # =====================================================
    # LOAD ALL PUBLISHED RESULTS
    # =====================================================

    all_results = list(results_collection.find({
        "student_id": student_id,
        "published": True
    }))

    # =====================================================
    # BUILD AVAILABLE SESSIONS
    # =====================================================

    sessions = sorted(
        list({
            r.get("session")
            for r in all_results
            if r.get("session")
        })
    )

    # =====================================================
    # BUILD AVAILABLE TERMS
    # =====================================================

    terms = [
        "First Term",
        "Second Term",
        "Third Term"
    ]

    # =====================================================
    # SELECT SESSION
    # =====================================================

    selected_session = request.args.get(
        "session",
        school.get("current_session", "")
    )

    # =====================================================
    # SELECT TERM
    # =====================================================

    selected_term = request.args.get(
        "term",
        school.get("current_term", "")
    )

    # =====================================================
    # LOAD SELECTED RESULT
    # =====================================================

    result = results_collection.find_one({

        "student_id": student_id,

        "session": {
            "$in": [
                selected_session,
                f"{selected_session} Academic Session"
            ]
        },

        "term": selected_term,

        "published": True

    })

    if not result:

        result = {}

    # =====================================================
    # ATTACH RESULT TO STUDENT
    # =====================================================

    student["results"] = result.get("results", {})
    student["attendance"] = result.get("attendance", {})
    student["affective"] = result.get("affective", {})
    student["psychomotor"] = result.get("psychomotor", {})

    student["position"] = result.get("position", "")
    student["teacher_remark"] = result.get("teacher_remark", "")
    student["principal_remark"] = result.get("principal_remark", "")
    student["promotion_status"] = result.get("promotion_status", "")
    student["next_term_begins"] = (result.get("next_term_begins")or school.get("next_term_begins", "")
)
    student["form_teacher"] = result.get("form_teacher", "")
    student["principal"] = result.get(
        "principal",
        school.get("principal", "")
    )

    # =====================================================
    # CALCULATE RESULT
    # =====================================================

    calculate_result(student)

    # =====================================================
    # CALCULATE CLASS POSITION
    # =====================================================

    class_students = list(
        students_collection.find({
            "class": student["class"]
        })
    )

    for s in class_students:
        calculate_result(s)

    class_students.sort(
        key=lambda x: (
            x.get("average_score", 0),
            x.get("total", 0)
        ),
        reverse=True
    )

    student_position = "-"

    for index, s in enumerate(class_students, start=1):

        if s["student_id"] == student["student_id"]:

            if index == 1:
                student_position = "1st"
            elif index == 2:
                student_position = "2nd"
            elif index == 3:
                student_position = "3rd"
            else:
                if 10 <= index % 100 <= 20:
                    suffix = "th"
                else:
                    suffix = {
                        1: "st",
                        2: "nd",
                        3: "rd"
                    }.get(index % 10, "th")

                student_position = f"{index}{suffix}"

            break

    student["position"] = student_position

    # =====================================================
    # PROMOTION STATUS
    # =====================================================

    if selected_term in ["First Term", "Second Term"]:

        student["promotion_status"] = "IN PROGRESS"

    else:

        student["promotion_status"] = result.get(
            "promotion_status",
            "PROMOTED"
        )

    # =====================================================
    # RENDER DASHBOARD
    # =====================================================

    return render_template(

        "student_dashboard.html",

        school=school,

        student=student,

        result=result,

        sessions=sessions,

        terms=terms,

        selected_session=selected_session,

        selected_term=selected_term,

        current_session=school.get("current_session", ""),

        current_term=school.get("current_term", "")

    )
# Student's Attendance Page
@app.route("/student/attendance")
@student_required
def student_attendance():

    student_id = session.get("student")

    student = students_collection.find_one({
        "student_id": student_id
    })

    if not student:

        flash(
            "Student not found.",
            "danger"
        )

        return redirect(
            url_for("student_login")
        )

    calculate_result(student)

    return render_template(

        "student_attendance.html",

        student=student,

        attendance=student.get(
            "attendance",
            {}
        ),

        school_name=SCHOOL_INFO["name"],

        school_logo=SCHOOL_INFO["logo"],

        current_term=SCHOOL_INFO["current_term"],

        current_session=SCHOOL_INFO["current_session"]

    )
# =========================================
# STUDENT PROFILE
# =========================================
@app.route("/student/profile")
@student_required
def student_profile():

    # ===============================
    # SCHOOL SETTINGS
    # ===============================

    school = get_school_settings()

    # ===============================
    # LOGGED IN STUDENT
    # ===============================

    student_id = session.get("student")

    if not student_id:
        return redirect(url_for("student_login"))

    student = students_collection.find_one({
        "student_id": str(student_id)
    })

    if not student:
        return redirect(url_for("student_login"))

    student.pop("_id", None)

    # ===============================
    # LOAD CURRENT RESULT
    # ===============================

    result = results_collection.find_one({

        "student_id": student_id,

        "session": {
            "$in": [
                school["current_session"],
                f'{school["current_session"]} Academic Session'
            ]
        },

        "term": school["current_term"],

        "published": True

    })

    if result:

        student["results"] = result.get("results", {})
        student["attendance"] = result.get("attendance", {})
        student["affective"] = result.get("affective", {})
        student["psychomotor"] = result.get("psychomotor", {})

        student["position"] = result.get("position", "")
        student["teacher_remark"] = result.get("teacher_remark", "")
        student["principal_remark"] = result.get("principal_remark", "")
        student["promotion_status"] = result.get("promotion_status", "")
        student["next_term_begins"] = result.get("next_term_begins", "")
        student["form_teacher"] = result.get("form_teacher", "")
        student["principal"] = result.get(
            "principal",
            school.get("principal", "")
        )

    # ===============================
    # CALCULATE SUMMARY
    # ===============================

    calculate_result(student)

    # ===============================
    # LOAD PROFILE
    # ===============================

    return render_template(

        "student_profile.html",

        student=student,

        school=school,

        current_session=school["current_session"],

        current_term=school["current_term"]

    )
# =========================
# VIEW STUDENT REPORT
# =========================
@app.route("/student_report/<student_id>")
def student_report(student_id):

    # =====================================================
    # PHASE 1
    # LOGIN VALIDATION
    # =====================================================

    if not session.get("admin") and not session.get("student"):

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("student_login")
        )
        # =====================================================
    # PHASE 2
    # LOAD STUDENT RECORD
    # =====================================================

    student = students_collection.find_one({
        "student_id": str(student_id)
    })

    if not student:

        flash(
            "Student not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    # Remove MongoDB ObjectId
    student.pop("_id", None)
        # =====================================================
    # PHASE 3
    # LOAD SCHOOL SETTINGS
    # =====================================================

    settings = get_school_settings()

    # =====================================================
    # SELECTED SESSION
    # =====================================================

    selected_session = (
        request.args.get("session")
        or settings.get("current_session")
    )

    # =====================================================
    # SELECTED TERM
    # =====================================================

    selected_term = (
        request.args.get("term")
        or settings.get("current_term")
    )

    # Save for template
    student["current_session"] = selected_session
    student["current_term"] = selected_term
        # =====================================================
    # PHASE 4
    # LOAD STUDENT REPORT
    # =====================================================

    report = results_collection.find_one({

        "student_id": str(student_id),

        "session": selected_session,

        "term": selected_term

    })

    if not report:

        flash(
            "No result found for this session and term.",
            "warning"
        )

        return redirect(
            url_for("reports")
        )

    # Remove MongoDB ObjectId
    report.pop("_id", None)

    # =====================================================
    # COPY REPORT DATA
    # =====================================================

    student["results"] = report.get("results", {})

    student["attendance"] = report.get("attendance", {})

    student["affective"] = report.get("affective", {})

    student["psychomotor"] = report.get("psychomotor", {})

    student["total_subjects"] = report.get("total_subjects", 0)

    student["total_score"] = report.get("total_score", 0)

    student["average_score"] = report.get("average_score", 0)

    student["percentage"] = report.get("percentage", 0)

    student["grade"] = report.get("grade", "-")

    student["remark"] = report.get("remark", "")

    student["position"] = report.get("position", "-")

    student["promotion_status"] = report.get("promotion_status", "")

    student["teacher_remark"] = report.get("teacher_remark", "")

    student["principal_remark"] = report.get("principal_remark", "")

    student["form_teacher"] = report.get("form_teacher", "")

    student["principal"] = report.get(
        "principal",
        settings.get("principal", "")
    )

    student["subjects_offered"] = report.get("subjects_offered", 0)

    student["subjects_passed"] = report.get("subjects_passed", 0)

    student["subjects_failed"] = report.get("subjects_failed", 0)

    print("=" * 60)
    print("REPORT LOADED SUCCESSFULLY")
    print(student["full_name"])
    print(selected_session)
    print(selected_term)
    print("=" * 60)
        # =====================================================
    # PHASE 5
    # LOAD FIRST, SECOND & THIRD TERM REPORTS
    # =====================================================

    first_term = results_collection.find_one({

        "student_id": str(student_id),

        "session": selected_session,

        "term": "First Term"

    })

    second_term = results_collection.find_one({

        "student_id": str(student_id),

        "session": selected_session,

        "term": "Second Term"

    })

    third_term = results_collection.find_one({

        "student_id": str(student_id),

        "session": selected_session,

        "term": "Third Term"

    })


    # =====================================================
    # STORE TERM TOTALS
    # =====================================================

    student["first_term_total"] = (
        first_term.get("total_score", 0)
        if first_term else 0
    )

    student["second_term_total"] = (
        second_term.get("total_score", 0)
        if second_term else 0
    )

    student["third_term_total"] = (
        third_term.get("total_score", 0)
        if third_term else 0
    )


    # =====================================================
    # STORE SUBJECTS OFFERED
    # =====================================================

    student["first_term_subjects"] = (
        first_term.get("total_subjects", 0)
        if first_term else 0
    )

    student["second_term_subjects"] = (
        second_term.get("total_subjects", 0)
        if second_term else 0
    )

    student["third_term_subjects"] = (
        third_term.get("total_subjects", 0)
        if third_term else 0
    )


    # =====================================================
    # STORE TERM AVERAGES
    # =====================================================

    student["first_term_average"] = (
        first_term.get("average_score", 0)
        if first_term else 0
    )

    student["second_term_average"] = (
        second_term.get("average_score", 0)
        if second_term else 0
    )

    student["third_term_average"] = (
        third_term.get("average_score", 0)
        if third_term else 0
    )


    print("=" * 60)
    print("TERM REPORTS LOADED")
    print("1st:", student["first_term_total"])
    print("2nd:", student["second_term_total"])
    print("3rd:", student["third_term_total"])
    print("=" * 60)
        # =====================================================
    # PHASE 6
    # CALCULATE CUMULATIVE PERFORMANCE
    # =====================================================

    cumulative_total = (

        student["first_term_total"]

        +

        student["second_term_total"]

        +

        student["third_term_total"]

    )

    cumulative_subjects = (

        student["first_term_subjects"]

        +

        student["second_term_subjects"]

        +

        student["third_term_subjects"]

    )

    if cumulative_subjects > 0:

        cumulative_average = round(

            cumulative_total / cumulative_subjects,

            2

        )

    else:

        cumulative_average = 0


    # =====================================================
    # CUMULATIVE GRADE & REMARK
    # =====================================================

    cumulative_grade, cumulative_remark = calculate_grade(

        cumulative_average

    )


    # =====================================================
    # SAVE CUMULATIVE VALUES
    # =====================================================

    student["cumulative_total"] = cumulative_total

    student["cumulative_subjects"] = cumulative_subjects

    student["cumulative_average"] = cumulative_average

    student["cumulative_grade"] = cumulative_grade

    student["cumulative_remark"] = cumulative_remark


    print("=" * 60)
    print("CUMULATIVE PERFORMANCE")
    print("Total:", cumulative_total)
    print("Subjects:", cumulative_subjects)
    print("Average:", cumulative_average)
    print("Grade:", cumulative_grade)
    print("=" * 60)
        # =====================================================
    # PHASE 7
    # CLASS POSITION & SUBJECT STATISTICS
    # =====================================================

    classmates = list(results_collection.find({

        "class": student.get("class"),

        "session": selected_session,

        "term": selected_term

    }))

    # -----------------------------
    # Overall Position
    # -----------------------------

    classmates.sort(

        key=lambda x: x.get("average_score", 0),

        reverse=True

    )

    student["position"] = "-"

    student["class_size"] = len(classmates)

    for index, record in enumerate(classmates, start=1):

        if record.get("student_id") == str(student_id):

            if index == 1:

                student["position"] = "1st"

            elif index == 2:

                student["position"] = "2nd"

            elif index == 3:

                student["position"] = "3rd"

            else:

                student["position"] = f"{index}th"

            break


    # -----------------------------
    # Subject Statistics
    # -----------------------------

    for subject in student["results"]:

        scores = []

        for record in classmates:

            result = record.get("results", {})

            if subject in result:

                scores.append({

                    "student_id": record["student_id"],

                    "total": result[subject].get("total", 0)

                })

        if scores:

            totals = [s["total"] for s in scores]

            highest = max(totals)

            lowest = min(totals)

            average = round(sum(totals) / len(totals), 2)

            scores.sort(

                key=lambda x: x["total"],

                reverse=True

            )

            subject_position = "-"

            for pos, s in enumerate(scores, start=1):

                if s["student_id"] == str(student_id):

                    if pos == 1:

                        subject_position = "1st"

                    elif pos == 2:

                        subject_position = "2nd"

                    elif pos == 3:

                        subject_position = "3rd"

                    else:

                        subject_position = f"{pos}th"

                    break

            student["results"][subject]["subject_position"] = subject_position

            student["results"][subject]["class_highest"] = highest

            student["results"][subject]["class_lowest"] = lowest

            student["results"][subject]["class_average"] = average

        else:

            student["results"][subject]["subject_position"] = "-"

            student["results"][subject]["class_highest"] = "-"

            student["results"][subject]["class_lowest"] = "-"

            student["results"][subject]["class_average"] = "-"
                # =====================================================
    # PHASE 8
    # PERFORMANCE REMARK & DOMAINS
    # =====================================================

    # -----------------------------
    # PERFORMANCE REMARK
    # -----------------------------

    average = student.get("average_score", 0)

    if average >= 85:

        student["performance_remark"] = "Excellent"

    elif average >= 75:

        student["performance_remark"] = "Very Good"

    elif average >= 65:

        student["performance_remark"] = "Good"

    elif average >= 50:

        student["performance_remark"] = "Fair"

    elif average >= 40:

        student["performance_remark"] = "Poor"

    else:

        student["performance_remark"] = "Very Poor"


    # -----------------------------
    # ATTENDANCE
    # -----------------------------

    student.setdefault("attendance", {})

    student["attendance"].setdefault("opened", 0)

    student["attendance"].setdefault("present", 0)

    student["attendance"].setdefault("absent", 0)

    if student["attendance"]["opened"] > 0:

        student["attendance"]["attendance_percentage"] = round(

            (

                student["attendance"]["present"]

                /

                student["attendance"]["opened"]

            ) * 100,

            2

        )

    else:

        student["attendance"]["attendance_percentage"] = 0


    # -----------------------------
    # AFFECTIVE DOMAIN
    # -----------------------------

    student.setdefault("affective", {})


    # -----------------------------
    # PSYCHOMOTOR DOMAIN
    # -----------------------------

    student.setdefault("psychomotor", {})
        # =====================================================
    # PHASE 9
    # SCHOOL INFORMATION & REMARKS
    # =====================================================

    # -----------------------------
    # Teacher & Principal
    # -----------------------------

    student["form_teacher"] = report.get(
        "form_teacher",
        settings.get("form_teacher", "")
    )

    student["principal"] = report.get(
        "principal",
        settings.get("principal", "")
    )


    # -----------------------------
    # Remarks
    # -----------------------------

    student["teacher_remark"] = report.get(
        "teacher_remark",
        ""
    )

    student["principal_remark"] = report.get(
        "principal_remark",
        ""
    )


    # -----------------------------
    # School Details
    # -----------------------------

    student["school_name"] = settings.get(
        "name",
        ""
    )

    student["school_address"] = settings.get(
        "address",
        ""
    )

    student["school_phone"] = settings.get(
        "phone",
        ""
    )

    student["school_email"] = settings.get(
        "email",
        ""
    )

    student["school_logo"] = settings.get(
        "logo",
        ""
    )

    student["school_motto"] = settings.get(
        "motto",
        ""
    )


    # -----------------------------
    # Important Dates
    # -----------------------------

    student["school_closed"] = settings.get(
        "school_closed",
        ""
    )

    student["next_term_begins"] = settings.get(
        "next_term_begins",
        ""
    )


    # -----------------------------
    # Session & Term
    # -----------------------------

    student["current_session"] = selected_session

    student["current_term"] = selected_term
        # =====================================================
    # PHASE 10
    # PREPARE TEMPLATE DATA
    # =====================================================

    cumulative = {

        "first_term_total": student["first_term_total"],

        "second_term_total": student["second_term_total"],

        "third_term_total": student["third_term_total"],

        "first_term_subjects": student["first_term_subjects"],

        "second_term_subjects": student["second_term_subjects"],

        "third_term_subjects": student["third_term_subjects"],

        "first_term_average": student["first_term_average"],

        "second_term_average": student["second_term_average"],

        "third_term_average": student["third_term_average"],

        "total": student["cumulative_total"],

        "subjects": student["cumulative_subjects"],

        "average": student["cumulative_average"],

        "grade": student["cumulative_grade"],

        "remark": student["cumulative_remark"]

    }


    # =====================================================
    # SUMMARY
    # =====================================================

    summary = {

        "total_subjects": student.get("total_subjects", 0),

        "subjects_offered": student.get("subjects_offered", 0),

        "subjects_passed": student.get("subjects_passed", 0),

        "subjects_failed": student.get("subjects_failed", 0),

        "total_score": student.get("total_score", 0),

        "average_score": student.get("average_score", 0),

        "percentage": student.get("percentage", 0),

        "grade": student.get("grade", "-"),

        "performance_remark": student.get("performance_remark", ""),

        "position": student.get("position", "-")

    }
        # =====================================================
    # PHASE 11
    # RENDER STUDENT REPORT
    # =====================================================

    return render_template(

        "student_report.html",

        # Student Information
        student=student,

        # Subject Results
        results=student.get("results", {}),

        # Attendance
        attendance=student.get("attendance", {}),

        # Affective Domain
        affective=student.get("affective", {}),

        # Psychomotor Domain
        psychomotor=student.get("psychomotor", {}),

        # Performance Summary
        summary=summary,

        # Cumulative Performance
        cumulative=cumulative,

        # School Information
        school=settings,

        school_name=settings.get("name"),

        school_logo=settings.get("logo"),

        school_address=settings.get("address"),

        school_phone=settings.get("phone"),

        school_email=settings.get("email"),

        school_motto=settings.get("motto"),

        # Academic Session
        current_session=selected_session,

        current_term=selected_term,

        # Dates
        school_closed=settings.get("school_closed"),

        next_term_date=settings.get("next_term_begins")

    )
@app.route("/admin/delete_student/<student_id>")
@admin_required
def delete_student(student_id):

    print("DELETE ROUTE")
    print("students_collection =", students_collection)
    print("type =", type(students_collection))

    students_collection.delete_one(
        {"student_id": student_id}
    )

    flash("Student deleted successfully.", "success")

    return redirect(url_for("dashboard"))
@app.route("/download_report/<student_id>")
def download_report(student_id):

    # ==========================================
    # GET STUDENT
    # ==========================================

    student = students_collection.find_one({

        "student_id": str(student_id)

    })

    if not student:

        return "Student not found"

    # ==========================================
    # GET SCHOOL SETTINGS
    # ==========================================

    settings = get_school_settings()

    selected_term = request.args.get(

        "term",

        settings["current_term"]

    )

    selected_session = request.args.get(

        "session",

        settings["current_session"]

    )

    # ==========================================
    # LOAD SAVED RESULT
    # ==========================================

    saved_result = results_collection.find_one({

        "student_id": str(student_id),

        "term": selected_term,

        "session": selected_session

    })

    if saved_result:

        student["results"] = saved_result.get("results", {})

        student["attendance"] = saved_result.get("attendance", {})

        student["affective"] = saved_result.get("affective", {})

        student["psychomotor"] = saved_result.get("psychomotor", {})

        student["total"] = saved_result.get("total_score", 0)

        student["average_score"] = saved_result.get("average_score", 0)

        student["grade"] = saved_result.get("grade", "F9")

        student["remark"] = saved_result.get("remark", "")

        student["position"] = saved_result.get("position", "-")

        student["promotion_status"] = saved_result.get(

            "promotion_status",

            "NOT PROMOTED"

        )

        student["class_teacher_remark"] = saved_result.get(

            "class_teacher_remark",

            ""

        )

        student["principal_remark"] = saved_result.get(

            "principal_remark",

            ""

        )

        student["form_teacher"] = saved_result.get(

            "form_teacher",

            ""

        )

        student["principal"] = saved_result.get(

            "principal",

            settings["principal"]

        )

        student["next_term_begins"] = saved_result.get(

            "next_term_begins",

            settings["next_term_begins"]

        )

    # ==========================================
    # CALCULATE SUMMARY
    # ==========================================

    calculate_result(student)

    # ==========================================
    # RENDER PDF
    # ==========================================

    html = render_template(

        "student_report.html",

        student=student,
        class_analysis=student["class_analysis"],

        results=student.get("results", {}),

        attendance=student.get("attendance", {}),

        affective=student.get("affective", {}),

        psychomotor=student.get("psychomotor", {}),

        school_name=settings["name"],

        school_info=settings,

        SCHOOL_INFO=settings,

        school_logo=settings["logo"],

        current_term=selected_term,

        current_session=selected_session,

        next_term_date=settings["next_term_begins"]

    )

    pdf = BytesIO()

    pisa.CreatePDF(html, dest=pdf)

    response = make_response(pdf.getvalue())

    response.headers["Content-Type"] = "application/pdf"

    response.headers["Content-Disposition"] = (
        f"attachment; filename={student.get('student_id', '')}_{selected_term.replace(' ', '_')}_{selected_session}_Result.pdf"
    )

    return response
# =========================================
# LOGOUT
# =========================================
@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("student_login")
    )

# =========================================
# ADMIN LOGOUT
# =========================================
@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )
# ==========================================================
# UPDATE STUDENT RESULT
# PHASE 1
# ==========================================================

@app.route("/admin/update_results/<student_id>", methods=["POST"])
@admin_required
def update_results(student_id):
    # ======================================================
    # CLEAN STUDENT ID
    # ======================================================

    student_id = str(student_id).strip()

    # ======================================================
    # GET STUDENT RECORD
    # ======================================================

    student = students_collection.find_one({

        "student_id": student_id

    })

    if not student:

        flash("Student not found.", "danger")

        return redirect(url_for("dashboard"))

    # ======================================================
    # LOAD SCHOOL SETTINGS
    # ======================================================

    settings = get_school_settings()

    # ======================================================
    # GET CURRENT SESSION & TERM
    # ======================================================

    selected_session = request.form.get(

        "session",

        settings.get("current_session")

    )

    selected_term = request.form.get(

        "term",

        settings.get("current_term")

    )

    # ======================================================
    # FIND SAVED RESULT
    # ======================================================

    saved_result = results_collection.find_one({

        "student_id": student_id,

        "session": selected_session,

        "term": selected_term

    })

    # ======================================================
    # LOAD EXISTING DATA
    # ======================================================

    if saved_result:

        results = saved_result.get("results", {})

        attendance = saved_result.get("attendance", {})

        affective = saved_result.get("affective", {})

        psychomotor = saved_result.get("psychomotor", {})

    else:

        results = student.get("results", {})

        attendance = {}

        affective = {}

        psychomotor = {}

    # ======================================================
    # CONTINUE TO PHASE 2
    # ======================================================
    # ======================================================
    # PHASE 2
    # READ SUBJECT SCORES
    # ======================================================

    updated_results = {}

    total_score = 0

    total_subjects = 0

    total_obtainable = 0

    passed_subjects = 0

    failed_subjects = 0

    # ==========================================
    # LOOP THROUGH ALL REGISTERED SUBJECTS
    # ==========================================

    for subject, old_result in results.items():

        # -------------------------------
        # Continuous Assessment
        # -------------------------------

        try:

            test = float(

                request.form.get(

                    f"{subject}_test",

                    old_result.get("test", 0)

                ) or 0

            )

        except (ValueError, TypeError):

            test = 0

        # -------------------------------
        # Examination
        # -------------------------------

        try:

            exam = float(

                request.form.get(

                    f"{subject}_exam",

                    old_result.get("exam", 0)

                ) or 0

            )

        except (ValueError, TypeError):

            exam = 0

        # -------------------------------
        # Subject Total
        # -------------------------------

        subject_total = round(test + exam, 2)

        # -------------------------------
        # Grade & Remark
        # -------------------------------

        grade, remark = calculate_grade(subject_total)

        # -------------------------------
        # Save Subject
        # -------------------------------

        updated_results[subject] = {

            "test": test,

            "exam": exam,

            "total": subject_total,

            "grade": grade,

            "remark": remark

        }

        # -------------------------------
        # Running Totals
        # -------------------------------

        total_score += subject_total

        total_subjects += 1

        total_obtainable += 100

        if subject_total >= 50:

            passed_subjects += 1

        else:

            failed_subjects += 1

    # ======================================================
    # CALCULATE ACADEMIC SUMMARY
    # ======================================================

    if total_subjects > 0:

        average_score = round(

            total_score / total_subjects,

            2

        )

    else:

        average_score = 0

    percentage = round(

        (total_score / total_obtainable) * 100,

        2

    ) if total_obtainable > 0 else 0

    # ======================================================
    # OVERALL GRADE
    # ======================================================

    overall_grade, overall_remark = calculate_grade(

        average_score

    ) 
    # ======================================================
    # PHASE 3
    # ATTENDANCE RECORD
    # ======================================================

    try:
        school_opened = int(

            request.form.get(

                "opened",

                attendance.get("opened", 0)

            ) or 0

        )

    except (ValueError, TypeError):

        school_opened = 0

    try:

        present = int(

            request.form.get(

                "present",

                attendance.get("present", 0)

            ) or 0

        )

    except (ValueError, TypeError):

        present = 0

    try:

        absent = int(

            request.form.get(

                "absent",

                attendance.get("absent", 0)

            ) or 0

        )

    except (ValueError, TypeError):

        absent = 0

    # ======================================================
    # CALCULATE ATTENDANCE PERCENTAGE
    # ======================================================

    if school_opened > 0:

        attendance_percentage = round(

            (present / school_opened) * 100,

            2

        )

    else:

        attendance_percentage = 0

    # ======================================================
    # SAVE ATTENDANCE
    # ======================================================

    attendance = {

        "opened": school_opened,

        "present": present,

        "absent": absent,

        "attendance_percentage": attendance_percentage

    }
    # ======================================================
    # PHASE 4
    # AFFECTIVE DOMAIN
    # ======================================================

    affective = {

        "attentiveness": request.form.get(

            "attentiveness",

            affective.get("attentiveness", "")

        ),

        "honesty": request.form.get(

            "honesty",

            affective.get("honesty", "")

        ),

        "neatness": request.form.get(

            "neatness",

            affective.get("neatness", "")

        ),

        "politeness": request.form.get(

            "politeness",

            affective.get("politeness", "")

        ),

        "punctuality_assembly": request.form.get(

            "punctuality_assembly",

            affective.get("punctuality_assembly", "")

        ),

        "self_control_calmness": request.form.get(

            "self_control_calmness",

            affective.get("self_control_calmness", "")

        ),

        "obedience": request.form.get(

            "obedience",

            affective.get("obedience", "")

        ),

        "reliability": request.form.get(

            "reliability",

            affective.get("reliability", "")

        ),

        "sense_of_responsibility": request.form.get(

            "sense_of_responsibility",

            affective.get("sense_of_responsibility", "")

        ),

        "relationship_with_others": request.form.get(

            "relationship_with_others",

            affective.get("relationship_with_others", "")

        )

    }
    # ======================================================
    # PHASE 5
    # PSYCHOMOTOR DOMAIN
    # ======================================================

    psychomotor = {

        "handling_of_tools": request.form.get(

            "handling_of_tools",

            psychomotor.get("handling_of_tools", "")

        ),

        "drawing_painting": request.form.get(

            "drawing_painting",

            psychomotor.get("drawing_painting", "")

        ),

        "handwriting": request.form.get(

            "handwriting",

            psychomotor.get("handwriting", "")

        ),

        "public_speaking": request.form.get(

            "public_speaking",

            psychomotor.get("public_speaking", "")

        ),

        "speech_fluency": request.form.get(

            "speech_fluency",

            psychomotor.get("speech_fluency", "")

        ),

        "sports_games": request.form.get(

            "sports_games",

            psychomotor.get("sports_games", "")

        )

    }
    # ======================================================
    # PHASE 6
    # RESULT SUMMARY & PROMOTION
    # ======================================================

    class_teacher_remark = request.form.get(

        "teacher_remark",

        ""

    )

    principal_remark = request.form.get(

        "principal_remark",

        ""

    )

    promotion_status = request.form.get(

        "promotion_status",

        "PROMOTED"

    )

    position = request.form.get(

        "position",

        "-"

    )

    form_teacher = request.form.get(

        "form_teacher",

        ""

    )

    principal = request.form.get(

        "principal",

        ""

    )

    next_term_begins = request.form.get(

        "next_term_begins",

        ""

    )

    school_closed = request.form.get(

        "school_closed",

        ""

    )

    # ======================================================
    # TOTALS
    # ======================================================

    total_obtainable = total_subjects * 100

    passed_subjects = sum(

        1

        for subject in updated_results.values()

        if subject["total"] >= 50

    )

    failed_subjects = sum(

        1

        for subject in updated_results.values()

        if subject["total"] < 50

    )

    # ======================================================
    # SAVE CURRENT TERM SUMMARY
    # ======================================================

    term_update = {}

    if selected_term == "First Term":

        term_update = {

            "first_term_subjects": total_subjects,

            "first_term_total": total_score,

            "first_term_average": average_score,

            "first_term_grade": overall_grade,

            "first_term_remark": overall_remark

        }

    elif selected_term == "Second Term":

        term_update = {

            "second_term_subjects": total_subjects,

            "second_term_total": total_score,

            "second_term_average": average_score,

            "second_term_grade": overall_grade,

            "second_term_remark": overall_remark

        }

    elif selected_term == "Third Term":

        term_update = {

            "third_term_subjects": total_subjects,

            "third_term_total": total_score,

            "third_term_average": average_score,

            "third_term_grade": overall_grade,

            "third_term_remark": overall_remark

        }
    # ======================================================
    # PHASE 7
    # SAVE RESULT TO RESULTS COLLECTION
    # ======================================================

    result_data = {

        "student_id": student_id,

        "student_name": student.get("full_name"),

        "registration_number": student.get("registration_number"),

        "roll_number": student.get("roll_number"),

        "class": student.get("class"),

        "arm": student.get("arm"),

        "gender": student.get("gender"),

        "session": selected_session,

        "term": selected_term,

        # =====================================
        # SUBJECT RESULTS
        # =====================================

        "results": updated_results,

        # =====================================
        # ATTENDANCE
        # =====================================

        "attendance": attendance,

        # =====================================
        # AFFECTIVE
        # =====================================

        "affective": affective,

        # =====================================
        # PSYCHOMOTOR
        # =====================================

        "psychomotor": psychomotor,

        # =====================================
        # SUMMARY
        # =====================================

        "total_subjects": total_subjects,

        "passed_subjects": passed_subjects,

        "failed_subjects": failed_subjects,

        "total_score": total_score,

        "total_obtainable": total_obtainable,

        "average_score": average_score,

        "percentage": percentage,

        "grade": overall_grade,

        "remark": overall_remark,

        # =====================================
        # POSITION
        # =====================================

        "position": position,

        "promotion_status": promotion_status,

        # =====================================
        # REMARKS
        # =====================================

        "teacher_remark": class_teacher_remark,

        "principal_remark": principal_remark,

        # =====================================
        # SCHOOL
        # =====================================

        "form_teacher": form_teacher,

        "principal": principal,

        "school_closed": school_closed,

        "next_term_begins": next_term_begins,

        # =====================================
        # TERM SUMMARY
        # =====================================

        **term_update

    }

    results_collection.update_one(

        {

            "student_id": student_id,

            "session": selected_session,

            "term": selected_term

        },

        {

            "$set": result_data

        },

        upsert=True

    )
    # ======================================================
    # PHASE 8
    # UPDATE STUDENT COLLECTION
    # ======================================================

    student_update = {

        # =====================================
        # CURRENT RESULT
        # =====================================

        "results": updated_results,

        "attendance": attendance,

        "affective": affective,

        "psychomotor": psychomotor,

        # =====================================
        # CURRENT SESSION
        # =====================================

        "session": selected_session,

        "term": selected_term,

        # =====================================
        # SUMMARY
        # =====================================

        "total_subjects": total_subjects,

        "passed_subjects": passed_subjects,

        "failed_subjects": failed_subjects,

        "total": total_score,

        "total_score": total_score,

        "total_obtainable": total_obtainable,

        "average_score": average_score,

        "percentage": percentage,

        "grade": overall_grade,

        "remark": overall_remark,

        # =====================================
        # POSITION
        # =====================================

        "position": position,

        "promotion_status": promotion_status,

        # =====================================
        # REMARKS
        # =====================================

        "teacher_remark": class_teacher_remark,

        "principal_remark": principal_remark,

        # =====================================
        # SCHOOL INFORMATION
        # =====================================

        "form_teacher": form_teacher,

        "principal": principal,

        "school_closed": school_closed,

        "next_term_begins": next_term_begins,

        # =====================================
        # TERM SUMMARY
        # =====================================

        **term_update

    }

    students_collection.update_one(

        {

            "student_id": student_id

        },

        {

            "$set": student_update

        }

    )

    # ======================================================
    # SUCCESS MESSAGE
    # ======================================================

    flash(

        f"{selected_term} ({selected_session}) results updated successfully.",

        "success"

    )

    return redirect(

        url_for(

            "edit_results",

            student_id=student_id,

            session=selected_session,

            term=selected_term

        )

    )

# =========================================
# CLASS MANAGEMENT
# =========================================

@app.route("/admin/classes")
@admin_required
def class_management():

    classes = classes_collection.find()

    return render_template(
        "class_management.html",
        classes=classes,
        school_name=SCHOOL_INFO["name"]
    )

@app.route("/classes")
@admin_required
def student_classes():

    students = list(students_collection.find())

    classes = {}

    for student in students:

        class_name = student.get("class", "Unknown")

        if class_name not in classes:

            classes[class_name] = {
                "teacher": "Not Assigned",
                "phone": "",
                "students": []
            }

        classes[class_name]["students"].append({
            "name": student.get("name"),
            "student_id": student.get("student_id"),
            "grade": student.get("grade", "-")
        })

    return render_template(
        "classes.html",
        classes=classes,
        total_students=len(students),
        school_name=SCHOOL_INFO["name"],
        school_logo=SCHOOL_INFO["logo"],
        current_term=SCHOOL_INFO["current_term"],
        current_session=SCHOOL_INFO["current_session"]
    )

@app.context_processor
def inject_school_data():

    total_students = 0

    if students_collection is not None:
        total_students = students_collection.count_documents({})

    return dict(
        school_name=SCHOOL_INFO["name"],
        school_logo=SCHOOL_INFO["logo"],
        current_term=SCHOOL_INFO["current_term"],
        current_session=SCHOOL_INFO["current_session"],
        total_students=total_students,
        total_classes=len(CLASSES)
    )

def teacher_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if not session.get("teacher_id"):

            return redirect(
                url_for("teacher_login")
            )

        return f(*args, **kwargs)

    return wrapper


@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():

    if request.method == "POST":

        teacher_id = request.form.get("teacher_id")
        password = request.form.get("password")
        teacher_phone = request.form.get("phone")

        teacher = teachers_collection.find_one(
            {"teacher_id": teacher_id}
        )

        if teacher and check_password_hash(
    teacher["teacher_password"],
    password
):

            session["teacher_id"] = teacher["teacher_id"]
            session["teacher_name"] = teacher["teacher_name"]
            session["teacher_class"] = teacher["teacher_class"]

            return redirect(url_for("teacher_dashboard"))

        flash("Invalid Login Details", "danger")

    return render_template("teacher_login.html")
@app.route("/teacher/dashboard")
@teacher_required
def teacher_dashboard():

    teacher = teachers_collection.find_one({
        "teacher_id": session.get("teacher_id")
    })

    if not teacher:
        flash("Teacher not found", "danger")
        return redirect(url_for("teacher_login"))

    teacher_class = teacher.get("class_assigned", "")

    students = list(
        students_collection.find({
            "class": teacher_class
        })
    )

    total_students = len(students)

    present_today = attendance_collection.count_documents({
        "class": teacher_class,
        "status": "Present"
    })

    absent_today = attendance_collection.count_documents({
        "class": teacher_class,
        "status": "Absent"
    })

    return render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        students=students,
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        class_name=teacher_class
    )

@app.route("/admin/edit_teacher/<teacher_id>", methods=["GET", "POST"])
@admin_required
def edit_teacher(teacher_id):

    teacher = teachers_collection.find_one({
        "teacher_id": teacher_id
    })

    if not teacher:
        flash("Teacher not found", "danger")
        return redirect(url_for("manage_teachers"))

    if request.method == "POST":

        teachers_collection.update_one(
            {"teacher_id": teacher_id},
            {
                "$set": {
                    "teacher_name": request.form["name"],
                    "email": request.form["email"],
                    "phone": request.form["phone"],
                    "class": request.form["class"]
                }
            }
        )

        flash("Teacher updated successfully", "success")

        return redirect(url_for("manage_teachers"))

    return render_template(
        "edit_teacher.html",
        teacher=teacher
    )


@app.route('/teacher/logout')
def teacher_logout():

    session.pop('teacher_id', None)
    session.pop('teacher_name', None)
    session.pop('teacher_class', None)

    flash(
        'Logged Out Successfully',
        'success'
    )

    return redirect(
        url_for('teacher_login')
    )


@app.route(
    "/teacher/attendance",
    methods=["GET", "POST"]
)
@teacher_required
def mark_attendance():
    teacher = teachers_collection.find_one({
    "teacher_id": session["teacher_id"]
})

    class_name = teacher["teacher_class"]

    students = list(
        students_collection.find({
            "class": class_name
        })
    )

    if request.method == "POST":

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        for student in students:

            status = request.form.get(
                student["student_id"]
            )
            attendance_collection.insert_one({
                "student_id": student["student_id"],
                "student_name": student["full_name"],
                "class": class_name,
                "date": today,
                "status": status,
                "marked_by": teacher["teacher_name"]
            })
        flash(
            "Attendance Saved Successfully",
            "success"
        )

        return redirect(
            url_for("teacher_dashboard")
        )

    return render_template(
        "mark_attendance.html",
        students=students
    )

@app.route("/attendance/history")
@teacher_required
def attendance_history():

    teacher_class = session.get("teacher_class")

    records = list(
        attendance_collection.find(
            {"class": teacher_class}
        ).sort("date", -1)
    )

    total_records = len(records)

    present = 0
    absent = 0

    for record in records:

        if record.get("status") == "Present":
            present += 1
        else:
            absent += 1

    attendance_rate = 0

    if total_records > 0:
        attendance_rate = round(
            (present / total_records) * 100,
            1
        )

    return render_template(
        "attendance_history.html",

        teacher_name=session.get("teacher_name"),

        teacher_class=teacher_class,

        records=records,

        total_records=total_records,

        present=present,

        absent=absent,

        attendance_rate=attendance_rate
    )


@app.route(
    "/student/checkin",
    methods=["GET", "POST"]
)
def student_checkin():

    if request.method == "POST":

        student_id = request.form.get(
            "student_id"
        )

        password = request.form.get(
            "password"
        )

        student = students_collection.find_one({
            "student_id": student_id
        })

        if not student:

            flash("Student Not Found")
            return redirect(
                url_for("student_checkin")
            )

        if not check_password_hash(
            student["password"],
            password
        ):

            flash("Invalid Password")
            return redirect(
                url_for("student_checkin")
            )

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        existing = attendance_collection.find_one({

            "student_id": student_id,

            "date": today

        })

        if existing:

            flash(
                "Already Checked In Today"
            )

            return redirect(
                url_for("student_checkin")
            )

        attendance_collection.insert_one({

            "student_id":
            student_id,

            "student_name":
            student["full_name"],

            "class":
            student["class"],

            "date":
            today,

            "time_in":
            datetime.now().strftime(
                "%I:%M %p"
            ),

            "time_out":
            "",

            "status":
            "Present"
        })

        flash(
            "Check In Successful"
        )

    return render_template(
        "student_checkin.html"
    )


@app.route(
    "/student/checkout",
    methods=["GET", "POST"]
)
def student_checkout():

    if request.method == "POST":

        student_id = request.form.get(
            "student_id"
        )

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        attendance_collection.update_one(

            {
                "student_id":
                student_id,

                "date":
                today
            },

            {
                "$set": {
                    "time_out":
                    datetime.now().strftime(
                        "%I:%M %p"
                    )
                }
            }
        )

        flash(
            "Check Out Successful"
        )

    return render_template(
        "student_checkout.html"
    )

@app.route("/qr_scanner")
@teacher_required
def qr_scanner():

    return render_template(
        "qr_scanner.html"
    )

@app.route(
    "/scan_qr",
    methods=["POST"]
)
def scan_qr():

    data = request.get_json()

    student_id = data.get(
        "student_id"
    )

    student = students_collection.find_one({
        "student_id": student_id
    })

    if not student:

        return jsonify({
            "message":
            "Student Not Found"
        })

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    current_time = datetime.now().strftime(
        "%I:%M %p"
    )

    attendance = attendance_collection.find_one({

        "student_id":
        student_id,

        "date":
        today
    })

    if attendance:

        attendance_collection.update_one(

            {
                "_id":
                attendance["_id"]
            },

            {
                "$set": {
                    "time_out":
                    current_time
                }
            }
        )

        return jsonify({
            "message":
            f"{student['full_name']} Checked Out"
        })

    attendance_collection.insert_one({

        "student_id":
        student_id,

        "student_name":
        student["full_name"],

        "class":
        student["class"],

        "date":
        today,

        "time_in":
        current_time,

        "time_out":
        ""
    })

    return jsonify({
        "message":
        f"{student['full_name']} Checked In"
    })
@app.route("/student/id_card/<student_id>")
@admin_required
def student_id_card(student_id):

    student = students_collection.find_one(
        {"student_id": student_id}
    )

    if not student:
        return "Student Not Found"

    qr_data = (
        f"http://127.0.0.1:5000/student/checkin/"
        f"{student['student_id']}"
    )

    qr = qrcode.make(qr_data)

    buffer = BytesIO()

    qr.save(buffer, format="PNG")

    qr_code = (
        "data:image/png;base64,"
        + base64.b64encode(
            buffer.getvalue()
        ).decode()
    )

    return render_template(
        "student_id_card.html",
        student=student,
        qr_code=qr_code
    )

@app.route("/admin/add_teacher", methods=["GET", "POST"])
@admin_required
def add_teacher():

    if request.method == "POST":

        teacher_name = request.form.get("teacher_name")
        teacher_id = request.form.get("teacher_id")
        teacher_email = request.form.get("teacher_email")
        teacher_password = request.form.get("teacher_password")
        teacher_class = request.form.get("teacher_class")
        teacher_phone = request.form.get("teacher_phone")
        teachers_collection.insert_one({
    "teacher_name": teacher_name,
    "teacher_id": teacher_id,
    "teacher_email": teacher_email,
    "teacher_password": generate_password_hash(teacher_password),
    "teacher_class": teacher_class,
    "teacher_phone": teacher_phone
})

        flash("Teacher Added Successfully", "success")

        return redirect(url_for("manage_teachers"))

    return render_template("add_teacher.html")
@app.route('/admin/delete_teacher/<teacher_id>')
@admin_required
def delete_teacher(teacher_id):

    teachers_collection.delete_one(
        {"teacher_id": teacher_id}
    )

    flash(
        'Teacher Deleted Successfully',
        'success'
    )

    return redirect(
        url_for('manage_teachers')
    )




@app.route("/admin/teachers")
@admin_required
def manage_teachers():

    teachers = list(
        teachers_collection.find()
    )

    return render_template(
        "manage_teachers.html",
        teachers=teachers
    )
@app.route("/teacher/profile")
@teacher_required
def teacher_profile():
    return "<h2>Teacher Profile</h2>"


@app.route("/teacher/classes")
@teacher_required
def teacher_classes():
    return "<h2>Teacher Classes</h2>"


@app.route("/teacher/students")
@teacher_required
def teacher_students():
    return "<h2>Teacher Students</h2>"


@app.route("/teacher/results")
@teacher_required
def teacher_results():
    return "<h2>Teacher Upload Results</h2>"

# =====================================================
# STUDENT REPORTS
# =====================================================

# @app.route("/student/reports")
# @login_required
# def student_reports():

#     student_id = session.get("student_id")

#     if not student_id:
#         flash("Please login first.", "danger")
#         return redirect(url_for("student_login"))

#     student = students_collection.find_one({
#         "student_id": student_id
#     })

#     reports = list(
#         results_collection.find(
#             {"student_id": student_id},
#             {"_id": 0}
#         ).sort([
#             ("session", -1),
#             ("term", 1)
#         ])
#     )

#     return render_template(
#         "student_reports.html",
#         student=student,
#         reports=reports
#     )
# =====================================================
# REPORTS PAGE
# =====================================================

@app.route("/admin/reports")
@admin_required
def reports():

    school = get_school_settings()

    students = list(students_collection.find())

    sessions = set()
    terms = set()

    for student in students:

        student.pop("_id", None)

        calculate_result(student)

        # Collect all sessions and terms from results
        student_results = list(
            results_collection.find(
                {"student_id": student["student_id"]}
            )
        )

        sessions.update(
            r.get("session", "")
            for r in student_results
            if r.get("session")
        )

        terms.update(
            r.get("term", "")
            for r in student_results
            if r.get("term")
        )

    return render_template(
        "reports.html",
        students=students,
        sessions=sorted(sessions),
        terms=sorted(terms),
        current_session=school.get("current_session"),
        current_term=school.get("current_term")
    )
@app.route("/admin/results")
@admin_required
def results():

    # =====================================
    # PHASE 1
    # LOAD SCHOOL SETTINGS
    # =====================================

    school = get_school_settings()

    # =====================================
    # PHASE 16
    # READ FILTERS
    # =====================================
    student_name = request.args.get("student_name", "").strip()

    student_id = request.args.get("student_id", "").strip()

    selected_class = request.args.get("class", "").strip()

    selected_session = (
        request.args.get("session")
        or get_school_settings().get("current_session", "")
    ).strip()

    # Remove " Academic Session" if it exists
    selected_session = selected_session.replace(" Academic Session", "")

    selected_term = (
        request.args.get("term")
        or get_school_settings().get("current_term", "")
    ).strip()
    # =====================================
    # PHASE 2
    # LOAD ALL STUDENTS
    # =====================================

        # =====================================
    # LOAD STUDENTS
    # =====================================

    query = {}

    if student_name:

        query["full_name"] = {
            "$regex": student_name,
            "$options": "i"
        }

    if student_id:

        query["student_id"] = student_id

    if selected_class:

        query["class"] = selected_class

    students = list(
        students_collection.find(query)
    )
        # =====================================
    # LOAD RESULT RECORDS
    # =====================================

    result_query = {}

    if selected_session:

        result_query["session"] = {
            "$in": [
                selected_session,
                f"{selected_session} Academic Session"
            ]
        }

    if selected_term:

        result_query["term"] = selected_term

    if selected_term:

        result_query["term"] = selected_term

    result_records = list(

        results_collection.find(result_query)

    )
    # =====================================
    # MATCH STUDENTS WITH RESULTS
    # =====================================

    if selected_session or selected_term:

        valid_ids = {

            r["student_id"]

            for r in result_records

        }

        students = [

            s for s in students

            if s["student_id"] in valid_ids

        ]
            # =====================================
    # ATTACH RESULT TO STUDENT
    # =====================================

    result_map = {}

    for r in result_records:

        result_map[r["student_id"]] = r

    for student in students:

        student["result"] = result_map.get(

            student["student_id"],

            {}

        )
    # =====================================
    # PHASE 3
    # INITIALIZE STATISTICS
    # =====================================

    grade_counts = {
        "A": 0,
        "B": 0,
        "C": 0,
        "F": 0
    }

    pending_results = 0
    approved_results = 0
    published_results = 0
    locked_results = 0

    # =====================================
    # PHASE 4
    # CALCULATE RESULTS
    # =====================================

    for student in students:

        student.pop("_id", None)

        result = student.get("result", {})

        # -----------------------------
        # Load academic values directly
        # -----------------------------

        student["average_score"] = result.get("average_score", 0)
        student["grade"] = result.get("grade", "-")
        student["remark"] = result.get("remark", "-")
        student["position"] = result.get("position", "-")

        approval_status = result.get(
            "approval_status",
            "Pending"
        )

        published = result.get(
            "published",
            False
        )

        locked = result.get(
            "locked",
            False
        )

        average = student["average_score"]

        grade = str(student["grade"])

        approval_status = result.get(
            "approval_status",
            "Pending"
        )

        published = result.get(
            "published",
            False
        )

        locked = result.get(
            "locked",
            False
        )

        average = student.get(
            "average_score",
            0
        )

        grade = str(
            student.get(
                "grade",
                ""
            )
        )

        # ==========================
        # Grade Statistics
        # ==========================

        if grade.startswith("A"):

            grade_counts["A"] += 1

        elif grade.startswith("B"):

            grade_counts["B"] += 1

        elif grade.startswith("C"):

            grade_counts["C"] += 1

        else:

            grade_counts["F"] += 1

        # ==========================
        # Approval Statistics
        # ==========================

        if approval_status == "Approved":

            approved_results += 1

        else:

            pending_results += 1

        # ==========================
        # Published Statistics
        # ==========================

        if published:

            published_results += 1

        # ==========================
        # Locked Statistics
        # ==========================

        if locked:

            locked_results += 1
    # =====================================
    # PHASE 5
    # TOP STUDENTS
    # =====================================

    top_students = sorted(

        students,

        key=lambda x: x.get("average_score", 0),

        reverse=True

    )[:10]

    # =====================================
    # PHASE 6
    # LOWEST STUDENTS
    # =====================================

    weak_students = sorted(

        students,

        key=lambda x: x.get("average_score", 0)

    )[:10]

    # =====================================
    # PHASE 7
    # SUBJECT ANALYSIS
    # =====================================

    subject_analysis = []

    subjects = {}

    for student in students:

        for subject, score in student.get("results", {}).items():

            total = score.get("total", 0)

            if subject not in subjects:

                subjects[subject] = {

                    "scores": [],

                    "best_student": "",

                    "highest": 0,

                    "lowest": 100

                }

            subjects[subject]["scores"].append(total)

            if total > subjects[subject]["highest"]:

                subjects[subject]["highest"] = total

                # Save the name of the student with the highest score
                subjects[subject]["best_student"] = student.get("full_name", "")

            if total < subjects[subject]["lowest"]:

                subjects[subject]["lowest"] = total

    for subject, data in subjects.items():

        scores = data["scores"]

        average = round(sum(scores) / len(scores), 2) if scores else 0

        pass_count = len([x for x in scores if x >= 50])

        fail_count = len(scores) - pass_count

        subject_analysis.append({

            "subject": subject,

            "highest": data["highest"],

            "lowest": data["lowest"],

            "average": average,

            "pass_count": pass_count,

            "fail_count": fail_count,

            "best_student": data["best_student"]

        })

    # We'll make this dynamic later.
    # For now keep it empty.

    # =====================================
    # PHASE 8
    # SUBJECT CHART DATA
    # =====================================

    subject_labels = []

    subject_averages = []

    for item in subject_analysis:

        subject_labels.append(item["subject"])

        subject_averages.append(item["average"])

    # =====================================
    # PHASE 9
    # AVAILABLE SESSIONS
    # =====================================

    sessions = [

        school.get("current_session")

    ]

    # =====================================
    # PHASE 10
    # ACTIVITY LOGS
    # =====================================

    activity_logs = []


    # =====================================
    # PHASE 11
    # RENDER TEMPLATE
    # =====================================

    return render_template(

            "results.html",
            student_name=student_name,
            student_id=student_id,
            selected_class=selected_class,
            selected_session=selected_session,
            selected_term=selected_term,
            school=school,

            students=students,

            sessions=sessions,

            grade_counts=grade_counts,

            top_students=top_students,

            weak_students=weak_students,

            subject_analysis=subject_analysis,

            pending_results=pending_results,

        approved_results=approved_results,

        published_results=published_results,

        locked_results=locked_results,
        subject_labels=subject_labels,
        subject_averages=subject_averages,

        activity_logs=activity_logs

    )
# =====================================================
# SCHOOL SETTINGS
# =====================================================

def get_school_settings():

    settings = settings_collection.find_one({
        "type": "school_settings"
    })

    defaults = {

        "type": "school_settings",

        "name": "Stella Maris College",

        "address": "",

        "phone": "",

        "email": "",

        "website": "",

        "motto": "Knowledge • Discipline • Excellence",

        "principal": "Mr Ransome Aremo",

        "current_session": "2025/2026",

        "current_term": "Third Term",

        "logo": "images/logo.png",

        "stamp": "images/school_stamp.png",

        "school_closed": "",

        "next_term_begins": ""

    }

    if not settings:

        settings = defaults.copy()

        settings_collection.insert_one(settings)

    else:

        changed = False

        for key, value in defaults.items():

            if key not in settings:

                settings[key] = value

                changed = True

        if changed:

            settings_collection.update_one(

                {"type": "school_settings"},

                {"$set": settings}

            )

    return settings
# =====================================
# PHASE 18
# APPROVE RESULT
# =====================================

@app.route("/admin/approve_result/<student_id>/<session>/<term>")
@admin_required
def approve_result(student_id, session, term):

    results_collection.update_one(

        {
            "student_id": student_id,
            "session": session,
            "term": term
        },

        {
            "$set": {
                "approval_status": "Approved"
            }
        }

    )
    save_activity(

        "Pending Result",

        student_id,

        session,

        term

    )


    flash(

        "Result approved successfully.",

        "success"

    )

    return redirect(url_for("results"))

@app.route("/admin/pending_result/<student_id>/<session>/<term>")
@admin_required
def pending_result(student_id, session, term):

    results_collection.update_one(

        {
            "student_id": student_id,
            "session": session,
            "term": term
        },

        {
            "$set": {
                "approval_status": "Pending"
            }
        }

    )

    # =====================================
    # SAVE ACTIVITY
    # =====================================

    save_activity(

        "Pending Result",

        student_id,

        session,

        term

    )

    flash(

        "Result moved to pending.",

        "warning"

    )

    return redirect(url_for("results"))
# =====================================================
# PHASE 18
# APPROVE ALL RESULTS
# =====================================================

@app.route("/admin/results/approve_all")
@admin_required
def approve_all_results():

    session = request.args.get("session")
    term = request.args.get("term")

    query = {}

    if session:
        query["session"] = session

    if term:
        query["term"] = term

    result = results_collection.update_many(

        query,

        {
            "$set": {
                "approval_status": "Approved"
            }
        }

    )

    save_activity(

        f"Approved All Results ({result.modified_count} records)",

        "",

        session,

        term

    )

    flash(

        f"{result.modified_count} result(s) approved successfully.",

        "success"

    )

    return redirect(url_for("results"))
# =====================================================
# PHASE 18
# PENDING ALL RESULTS
# =====================================================

@app.route("/admin/results/pending_all")
@admin_required
def pending_all_results():

    session = request.args.get("session")
    term = request.args.get("term")

    query = {}

    if session:
        query["session"] = session

    if term:
        query["term"] = term

    result = results_collection.update_many(

        query,

        {

            "$set": {

                "approval_status": "Pending"

            }

        }

    )

    # =====================================
    # SAVE ACTIVITY
    # =====================================

    save_activity(

        f"Pending All Results ({result.modified_count} records)",

        "",

        session,

        term

    )

    flash(

        f"{result.modified_count} result(s) changed to Pending.",

        "warning"

    )

    return redirect(url_for("results"))
# =====================================================
# PHASE 18
# PUBLISH ALL RESULTS
# =====================================================

@app.route("/admin/results/publish_all")
@admin_required
def publish_all_results():

    session = request.args.get("session")
    term = request.args.get("term")

    query = {}

    if session:
        query["session"] = session

    if term:
        query["term"] = term

    result = results_collection.update_many(

        query,

        {

            "$set": {

                "published": True

            }

        }

    )

    # =====================================
    # SAVE ACTIVITY
    # =====================================

    save_activity(

        f"Published All Results ({result.modified_count} records)",

        "",

        session,

        term

    )

    flash(

        f"{result.modified_count} result(s) published successfully.",

        "success"

    )

    return redirect(url_for("results"))
# =====================================================
# PHASE 18
# LOCK ALL RESULTS
# =====================================================

# =====================================================
# PHASE 18
# LOCK ALL RESULTS
# =====================================================

@app.route("/admin/results/lock_all")
@admin_required
def lock_all_results():

    # =====================================
    # READ FILTERS
    # =====================================

    session = request.args.get("session", "").strip()
    term = request.args.get("term", "").strip()

    # =====================================
    # BUILD QUERY
    # =====================================

    query = {}

    if session:
        query["session"] = session

    if term:
        query["term"] = term

    # =====================================
    # LOCK RESULTS
    # =====================================

    result = results_collection.update_many(

        query,

        {
            "$set": {
                "locked": True
            }
        }

    )

    # =====================================
    # SAVE ACTIVITY
    # =====================================

    save_activity(

        f"Locked All Results ({result.modified_count} records)",

        "",

        session,

        term

    )

    # =====================================
    # SUCCESS MESSAGE
    # =====================================

    flash(

        f"{result.modified_count} result(s) locked successfully.",

        "success"

    )

    return redirect(url_for("results"))
# =====================================================
# PHASE 18
# UNLOCK ALL RESULTS
# =====================================================

@app.route("/admin/results/unlock_all")
@admin_required
def unlock_all_results():

    # =====================================
    # READ FILTERS
    # =====================================

    session = request.args.get("session", "").strip()
    term = request.args.get("term", "").strip()

    # =====================================
    # BUILD QUERY
    # =====================================

    query = {}

    if session:
        query["session"] = session

    if term:
        query["term"] = term

    # =====================================
    # UNLOCK RESULTS
    # =====================================

    result = results_collection.update_many(

        query,

        {
            "$set": {
                "locked": False
            }
        }

    )

    # =====================================
    # SAVE ACTIVITY
    # =====================================

    save_activity(

        f"Unlocked All Results ({result.modified_count} records)",

        "",

        session,

        term

    )

    # =====================================
    # SUCCESS MESSAGE
    # =====================================

    flash(

        f"{result.modified_count} result(s) unlocked successfully.",

        "success"

    )

    return redirect(url_for("results"))
# =====================================================
# SETTINGS PAGE
# =====================================================

@app.route("/admin/settings")
@admin_required
def portal_settings():

    school = get_school_settings()

    return render_template(
        "settings.html",
        school=school
    )


# =====================================================
# UPDATE SCHOOL INFORMATION
# =====================================================

@app.route("/admin/update_school_settings", methods=["POST"])
@admin_required
def update_school_settings():

    settings_collection.update_one(

        {"type": "school_settings"},

        {
            "$set": {

                "name": request.form.get("name"),
                "address": request.form.get("address"),
                "phone": request.form.get("phone"),
                "email": request.form.get("email"),
                "website": request.form.get("website"),
                "motto": request.form.get("motto"),

                "principal": request.form.get("principal"),

                "school_closed": request.form.get("school_closed") or "",
                "next_term_begins": request.form.get("next_term_begins") or "",

                "logo": request.form.get("logo"),
                "stamp": request.form.get("stamp")

            }
        },

        upsert=True

    )

    flash("School information updated successfully.", "success")

    return redirect(url_for("portal_settings"))
print(settings_collection.find_one({"type": "school_settings"}))
# =====================================================
# UPDATE ACADEMIC SETTINGS
# =====================================================

@app.route("/admin/update_academic_settings", methods=["POST"])
@admin_required
def update_academic_settings():

    settings_collection.update_one(

        {
            "type": "school_settings"
        },

        {
            "$set": {

                "current_term": request.form.get("current_term"),

                "current_session": request.form.get("current_session"),

                "school_closed": request.form.get("school_closed") or "",

                "next_term_begins": request.form.get("next_term_begins") or ""

            }

        },

        upsert=True

    )

    flash("Academic settings updated successfully.", "success")

    return redirect(url_for("portal_settings"))
# ==========================================
# UPDATE SYSTEM SETTINGS
# ==========================================

@app.route("/admin/update_system_settings", methods=["POST"])
@admin_required
def update_system_settings():

    settings_collection.update_one(

        {
            "type": "school_settings"
        },

        {
            "$set": {

                "school_type": request.form.get("school_type"),

                "result_approval": request.form.get("result_approval"),

                "student_login": request.form.get("student_login"),

                "parent_login": request.form.get("parent_login"),

                "teacher_login": request.form.get("teacher_login"),

                "maximum_subjects": int(
                    request.form.get("maximum_subjects", 20)
                ),

                "portal_notice": request.form.get("portal_notice")

            }

        },

        upsert=True

    )

    flash(
        "System configuration updated successfully.",
        "success"
    )

    return redirect(
        url_for("portal_settings")
    )
# ==========================================
# UPDATE PORTAL APPEARANCE
# ==========================================

@app.route("/admin/update_portal_appearance", methods=["POST"])
@admin_required
def update_portal_appearance():

    update_data = {

        "portal_title": request.form.get("portal_title"),

        "theme_color": request.form.get("theme_color"),

        "footer_text": request.form.get("footer_text")

    }

    # LOGO
    logo = request.files.get("logo")

    if logo and logo.filename:

        filename = secure_filename(logo.filename)

        logo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        update_data["logo"] = "uploads/" + filename

    # STAMP
    stamp = request.files.get("stamp")

    if stamp and stamp.filename:

        filename = secure_filename(stamp.filename)

        stamp.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        update_data["stamp"] = "uploads/" + filename

    # BANNER
    banner = request.files.get("banner")

    if banner and banner.filename:

        filename = secure_filename(banner.filename)

        banner.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        update_data["banner"] = "uploads/" + filename

    # FAVICON
    favicon = request.files.get("favicon")

    if favicon and favicon.filename:

        filename = secure_filename(favicon.filename)

        favicon.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        update_data["favicon"] = "uploads/" + filename

    settings_collection.update_one(

        {

            "type": "school_settings"

        },

        {

            "$set": update_data

        },

        upsert=True

    )

    flash(

        "Portal appearance updated successfully.",

        "success"

    )

    return redirect(

        url_for("portal_settings")

    )
@app.route("/admin/publish_result/<result_id>")
@admin_required
def publish_result(result_id):

    results_collection.update_one(

        {
            "_id": ObjectId(result_id)
        },

        {
            "$set": {

                "published": True

            }

        }

    )

    flash(

        "Result has been published successfully.",

        "success"

    )

    return redirect(request.referrer or url_for("dashboard"))
@app.route("/admin/upload_results")
@admin_required
def upload_results():

    # =====================================
    # PHASE 1
    # LOAD SCHOOL SETTINGS
    # =====================================

    school = get_school_settings()

    # =====================================
    # PHASE 2
    # LOAD AVAILABLE SESSIONS
    # =====================================

    sessions = results_collection.distinct("session")

    if not sessions:
        sessions = [school.get("current_session", "")]

    # =====================================
    # PHASE 3
    # READ FILTERS
    # =====================================

    selected_session = request.args.get(
        "session",
        school.get("current_session", "")
    )

    selected_term = request.args.get(
        "term",
        school.get("current_term", "")
    )

    # Support BOTH class_ and class
    selected_class = request.args.get("class_", "").strip()

    if not selected_class:
        selected_class = request.args.get("class", "").strip()

    selected_subject = request.args.get(
        "subject",
        ""
    ).strip()

    # =====================================
    # PHASE 4
    # LOAD STUDENTS
    # =====================================

    students = []

    if selected_class:

        students = list(

            students_collection.find(

                {
                    "class": selected_class
                }

            ).sort("full_name", 1)

        )

    # =====================================
    # PHASE 5
    # OPEN PAGE
    # =====================================

    return render_template(

        "upload_results.html",

        school=school,

        sessions=sessions,

        students=students,

        selected_session=selected_session,

        selected_term=selected_term,

        selected_class=selected_class,

        selected_subject=selected_subject

    )
@app.route("/admin/enter_result/<student_id>", methods=["GET", "POST"])
@admin_required
def enter_result(student_id):

    # =====================================
    # LOAD STUDENT
    # =====================================

    student = students_collection.find_one({
        "student_id": student_id
    })

    if not student:

        flash("Student not found.", "danger")

        return redirect(url_for("upload_results"))

    # =====================================
    # READ PARAMETERS
    # =====================================

    session = request.args.get("session", "").strip()

    term = request.args.get("term", "").strip()

    subject = request.args.get("subject", "").strip()

    # =====================================
    # LOAD EXISTING RESULT
    # =====================================

    existing_result = results_collection.find_one({

        "student_id": student_id,

        "session": session,

        "term": term

    })

    # =====================================
    # LOCK CHECK
    # =====================================

    if existing_result and existing_result.get("locked", False):

        flash(
            "This result has been locked and cannot be edited.",
            "danger"
        )

        return redirect(url_for("results"))

    # =====================================
    # SAVE RESULT
    # =====================================

    if request.method == "POST":

        ca1 = int(request.form.get("ca1", 0))
        ca2 = int(request.form.get("ca2", 0))
        exam = int(request.form.get("exam", 0))

        total = ca1 + ca2 + exam

        if total >= 75:
            grade = "A"
            remark = "Excellent"

        elif total >= 65:
            grade = "B"
            remark = "Very Good"

        elif total >= 50:
            grade = "C"
            remark = "Good"

        elif total >= 40:
            grade = "D"
            remark = "Fair"

        else:
            grade = "F"
            remark = "Fail"

        subject_result = {

            "ca1": ca1,
            "ca2": ca2,
            "exam": exam,
            "total": total,
            "grade": grade,
            "remark": remark

        }

        # =====================================
        # UPDATE OR INSERT
        # =====================================

        if existing_result:

            results_collection.update_one(

                {"_id": existing_result["_id"]},

                {
                    "$set": {

                        f"results.{subject}": subject_result,

                        "student_name": student["full_name"],

                        "class": student["class"]

                    }
                }

            )

        else:

            results_collection.insert_one({

                "student_id": student_id,

                "student_name": student["full_name"],

                "class": student["class"],

                "session": session,

                "term": term,

                "results": {

                    subject: subject_result

                },

                "approval_status": "Pending",

                "published": False,

                "locked": False

            })

        # =====================================
        # RECALCULATE RESULT
        # =====================================

        updated_result = results_collection.find_one({

            "student_id": student_id,

            "session": session,

            "term": term

        })

        subjects = updated_result.get("results", {})

        subject_count = len(subjects)

        total_score = 0

        passed = 0

        failed = 0

        for score in subjects.values():

            mark = score.get("total", 0)

            total_score += mark

            if mark >= 50:
                passed += 1
            else:
                failed += 1

        average = round(
            total_score / subject_count,
            2
        ) if subject_count else 0

        results_collection.update_one(

            {"_id": updated_result["_id"]},

            {
                "$set": {

                    "total_score": total_score,

                    "average_score": average,

                    "subjects_offered": subject_count,

                    "subjects_passed": passed,

                    "subjects_failed": failed

                }

            }

        )
        recalculate_positions(
            session,
            term,
            student["class"]
        )

        # =====================================
        # ACTIVITY
        # =====================================

        save_activity(

            "Uploaded Result",

            student["full_name"],

            session,

            term

        )

        flash(

            "Result saved successfully.",

            "success"

        )


        return redirect(

            url_for(

                "upload_results",

                session=session,

                term=term,

                **{"class": student["class"]},

                subject=subject

            )

        )

    # =====================================
    # LOAD SUBJECT FOR EDITING
    # =====================================

    result = {}

    if existing_result:

        result = existing_result.get("results", {}).get(subject, {})

    # =====================================
    # OPEN PAGE
    # =====================================
    print(existing_result)

    print(subject)

    print(result)

    return render_template(

        "enter_result.html",

        student=student,

        result=result,

        session=session,

        term=term,

        subject=subject

    )
# @app.route("/teacher/logout")
# def teacher_logout():

#     session.pop("teacher_logged_in", None)
#     session.pop("teacher_id", None)
#     session.pop("teacher_name", None)

#     flash("Logged out successfully.", "success")

#     return redirect(url_for("teacher_login"))

# =========================================
# RUN APP
# =========================================
@app.route("/approve_selected_results", methods=["POST"])
@admin_required
def approve_selected_results():

    data = request.get_json()

    students = data.get("students", [])
    session = data.get("session", "").strip()
    term = data.get("term", "").strip()

    updated = 0

    print("=" * 60)
    print("APPROVE SELECTED")
    print("Students:", students)
    print("Session:", session)
    print("Term:", term)
    print("=" * 60)

    for student_id in students:

        result = results_collection.update_one(

            {
                "student_id": student_id,

                "session": {
                    "$in": [
                        session,
                        f"{session} Academic Session"
                    ]
                },

                "term": term
            },

            {
                "$set": {
                    "approval_status": "Approved"
                }
            }

        )

        print("Checking:", student_id)
        print("Modified:", result.modified_count)

        updated += result.modified_count

    return jsonify({
        "success": True,
        "message": f"{updated} result(s) approved successfully."
    })
@app.route("/publish_selected_results", methods=["POST"])
@admin_required
def publish_selected_results():

    data = request.get_json()

    students = data.get("students", [])
    session = data.get("session", "").strip()
    term = data.get("term", "").strip()

    updated = 0

    print("=" * 60)
    print("PUBLISH SELECTED")
    print("Students:", students)
    print("Session:", session)
    print("Term:", term)
    print("=" * 60)

    for student_id in students:

        doc = results_collection.find_one({

            "student_id": student_id,

            "session": {
                "$in": [
                    session,
                    f"{session} Academic Session"
                ]
            },

            "term": term

        })

        print("Document Found:", doc)

        result = results_collection.update_one(

            {
                "student_id": student_id,

                "session": {
                    "$in": [
                        session,
                        f"{session} Academic Session"
                    ]
                },

                "term": term
            },

            {
                "$set": {
                    "published": True,
                    "published_date": datetime.now()
                }
            }

        )

        print("Matched:", result.matched_count)
        print("Modified:", result.modified_count)

        updated += result.modified_count

    return jsonify({

        "success": True,

        "message": f"{updated} result(s) published successfully."

    })
@app.route("/lock_selected_results", methods=["POST"])
@admin_required
def lock_selected_results():

    data = request.get_json()

    students = data.get("students", [])
    session = data.get("session", "").strip()
    term = data.get("term", "").strip()

    updated = 0

    print("=" * 60)
    print("LOCK SELECTED")
    print("Students:", students)
    print("Session:", session)
    print("Term:", term)
    print("=" * 60)

    for student_id in students:

        doc = results_collection.find_one({

            "student_id": student_id,

            "session": {
                "$in": [
                    session,
                    f"{session} Academic Session"
                ]
            },

            "term": term

        })

        print("Document Found:", doc)

        result = results_collection.update_one(

            {
                "student_id": student_id,

                "session": {
                    "$in": [
                        session,
                        f"{session} Academic Session"
                    ]
                },

                "term": term
            },

            {
                "$set": {
                    "locked": True,
                    "locked_date": datetime.now()
                }
            }

        )

        print("Matched:", result.matched_count)
        print("Modified:", result.modified_count)

        updated += result.modified_count

    return jsonify({

        "success": True,

        "message": f"{updated} result(s) locked successfully."

    })
@app.route("/unlock_selected_results", methods=["POST"])
@admin_required
def unlock_selected_results():

    data = request.get_json()

    students = data.get("students", [])
    session = data.get("session", "").strip()
    term = data.get("term", "").strip()

    updated = 0

    for student_id in students:

        result = results_collection.update_one(

            {
                "student_id": student_id,

                "session": {
                    "$in": [
                        session,
                        f"{session} Academic Session"
                    ]
                },

                "term": term
            },

            {
                "$set": {
                    "locked": False,
                    "unlocked_date": datetime.now()
                }
            }

        )

        updated += result.modified_count

    return jsonify({

        "success": True,

        "message": f"{updated} result(s) unlocked successfully."

    })
@app.route("/admin/broadsheet")
@admin_required
def broadsheet():

    # =====================================================
    # PHASE 1
    # LOAD SCHOOL SETTINGS, FILTERS, STUDENTS, RESULTS
    # =====================================================

    school = get_school_settings()

    sessions = sorted(results_collection.distinct("session")) if results_collection is not None else []
    classes = sorted(students_collection.distinct("class")) if students_collection is not None else []

    selected_session = request.args.get(
        "session",
        school.get("current_session", "")
    ).strip()

    selected_term = request.args.get(
        "term",
        school.get("current_term", "")
    ).strip()

    selected_class = request.args.get(
        "class",
        ""
    ).strip()

    # Default to the first class so the page is not blank on first load
    if not selected_class and classes:
        selected_class = classes[0]

    students = []
    if students_collection is not None and selected_class:
        students = list(
            students_collection.find({
                "class": selected_class
            })
        )

    results = []
    if results_collection is not None and selected_class and selected_session and selected_term:
        results = list(
            results_collection.find({
                "class": selected_class,
                "term": selected_term,
                "session": {
                    "$in": [
                        selected_session,
                        f"{selected_session} Academic Session"
                    ]
                }
            })
        )

    result_map = {}
    for r in results:
        student_id = r.get("student_id")
        if student_id:
            result_map[str(student_id)] = r

    # =====================================================
    # PHASE 1B
    # ATTACH RESULTS TO STUDENTS
    # =====================================================

    for student in students:
        result = result_map.get(str(student.get("student_id")), {}) or {}

        student["result"] = result
        student["results"] = result.get("results", {})
        student["attendance"] = result.get("attendance", {})
        student["affective"] = result.get("affective", {})
        student["psychomotor"] = result.get("psychomotor", {})

        student["teacher_remark"] = result.get("teacher_remark", "")
        student["principal_remark"] = result.get("principal_remark", "")
        student["form_teacher"] = result.get("form_teacher", "")
        student["principal"] = result.get("principal", school.get("principal", ""))

        student["school_closed"] = result.get(
            "school_closed",
            school.get("school_closed", "")
        )

        student["next_term_begins"] = result.get(
            "next_term_begins",
            school.get("next_term_begins", "")
        )

        # =====================================================
        # PHASE 2
        # CALCULATE STUDENT RESULTS
        # =====================================================

        calculate_result(student)

        # Broadsheet uses percentage display
        student["percentage"] = round(student.get("average_score", 0), 2)

    # =====================================================
    # PHASE 2B
    # CLASS POSITIONS
    # =====================================================

    students.sort(
        key=lambda x: (
            x.get("average_score", 0),
            x.get("total", 0)
        ),
        reverse=True
    )

    # -----------------------------------------
    # Position Formatter
    # -----------------------------------------

    def ordinal(n):
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {
                1: "st",
                2: "nd",
                3: "rd"
            }.get(n % 10, "th")

        return f"{n}{suffix}"

    # -----------------------------------------
    # Assign Position
    # -----------------------------------------

    for index, student in enumerate(students, start=1):

        student["position"] = ordinal(index)

    # =====================================================
    # PHASE 3
    # BUILD SUBJECT LIST
    # =====================================================

    subjects = []

    for subject in SUBJECTS:
        if any(subject in (student.get("results", {}) or {}) for student in students):
            subjects.append(subject)

    # Add any extra subjects found in results that are not in SUBJECTS
    for student in students:
        for subject in (student.get("results", {}) or {}).keys():
            if subject not in subjects:
                subjects.append(subject)

    # =====================================================
    # PHASE 3B
    # SUBJECT SHORT NAMES
    # =====================================================

    subject_short_names = {
        "English Language": "ENG",
        "Mathematics": "MTH",
        "Further Mathematics": "FMTH",
        "Biology": "BIO",
        "Chemistry": "CHE",
        "Physics": "PHY",
        "Agricultural Science": "AGRIC",
        "Digital Technology": "DIGITAL",
        "C.R.S": "C.R.S",
        "C.C.A": "C.C.A",
        "Home Economics": "HOME ECON",
        "Social Studies": "SOC STUD",
        "French": "FRE",
        "Yoruba": "YOR",
        "Physical and Health Education": "PHE",
        "Music": "MUS",
        "Business Studies": "BST",
        "Intermediate Science": "INT. SCI",
        "Commerce": "COMM",
        "Technical Drawing": "TD",
        "Accounting": "ACC",
        "Economics": "ECO",
        "Government": "GOV",
        "Literature": "LIT",
        "Citizenship Education": "CVE",
        "Marketing": "MKT"
    }

    # =====================================================
    # PHASE 3C
    # SUBJECT STATISTICS
    # =====================================================

    subject_statistics = {}

    for subject in subjects:

        scores = []

        for student in students:

            mark = student.get("results", {}).get(subject, {}).get("total", 0)

            try:
                mark = float(mark)
            except Exception:
                mark = 0

            scores.append(mark)

        if scores:
            subject_statistics[subject] = {
                "highest": max(scores),
                "lowest": min(scores),
                "average": round(sum(scores) / len(scores), 2),
                "pass": len([x for x in scores if x >= 50]),
                "fail": len([x for x in scores if x < 50]),
            }
        else:
            subject_statistics[subject] = {
                "highest": 0,
                "lowest": 0,
                "average": 0,
                "pass": 0,
                "fail": 0,
            }

    # =====================================================
    # RENDER PAGE
    # =====================================================

    return render_template(
        "broadsheet.html",
        school=school,
        sessions=sessions,
        classes=classes,
        students=students,
        subjects=subjects,
        subject_statistics=subject_statistics,
        subject_short_names=subject_short_names,
        selected_session=selected_session,
        selected_term=selected_term,
        selected_class=selected_class,
        session=selected_session,
        term=selected_term,
        class_name=selected_class
    )


@app.route("/admin/generate_broadsheet")
@admin_required
def generate_broadsheet():
    return redirect(url_for(
        "broadsheet",
        **{
            "session": request.args.get("session", ""),
            "term": request.args.get("term", ""),
            "class": request.args.get("class", "")
        }
    ))
    # =====================================================
    # LOAD RESULTS
    # =====================================================

    results = list(

        results_collection.find({

            "class": selected_class,

            "term": term,

            "session": {

                "$in": [

                    session,

                    f"{session} Academic Session"

                ]

            }

        })

    )

    # =====================================================
    # MAP RESULTS TO STUDENTS
    # =====================================================

    result_map = {}

    for result in results:

        result_map[result["student_id"]] = result

    # =====================================================
    # ATTACH RESULTS
    # =====================================================

    for student in students:

        result = result_map.get(

            student["student_id"],

            {}

        )

        student["result"] = result

    # =====================================================
    # GET ALL SUBJECTS
    # =====================================================

    subjects = []

    for student in students:

        result = student.get("result", {})

        subject_results = result.get(

            "results",

            {}

        )

        for subject in subject_results.keys():

            if subject not in subjects:

                subjects.append(subject)

    subjects = sorted(subjects)

    # =====================================================
    # CALCULATE TOTALS
    # =====================================================

    for student in students:

        result = student.get("result", {})

        student["total"] = result.get(

            "total",

            0

        )

        student["percentage"] = result.get(

            "percentage",

            0

        )

        student["average"] = result.get(

            "average_score",

            0

        )

        student["grade"] = result.get(

            "grade",

            "-"

        )

        student["position"] = result.get(

            "position",

            "-"

        )

        student["remark"] = result.get(

            "remark",

            "-"

        )

    # =====================================================
    # SORT BY POSITION
    # =====================================================

    students = sorted(

        students,

        key=lambda x: (

            x["position"]

            if isinstance(

                x["position"],

                int

            )

            else 9999

        )

    )
    # =====================================
    # SUBJECT SHORT NAMES
    # =====================================

# =====================================
# SUBJECT SHORT NAMES
# =====================================

    subject_short_names = {

        "English Language": "ENG",
        "Mathematics": "MTH",
        "Further Mathematics": "FMTH",
        "Biology": "BIO",
        "Chemistry": "CHE",
        "Physics": "PHY",
        "Agricultural Science": "AGRIC",
        "Digital Technology": "DIGITAL",
        "Civic Education": "CIVIC",
        "Economics": "ECO",
        "Financial Accounting": "ACC",
        "Commerce": "COMM",
        "Government": "GOV",
        "Literature in English": "LIT",
        "Geography": "GEO",
        "History": "HIS",
        "CRS": "CRS",
        "Intermediate Science": "INT. SCI",
        "Yoruba": "YOR",    
        "French": "FRE",
        "Music": "MUS",
        "Technical Drawing": "TD",
        "Business Studies": "BST"

    }
        # =====================================
    # SUBJECT STATISTICS
    # =====================================

    subject_statistics = {}

    for subject in subjects:

        scores = []

        for student in students:

            result = student.get("result", {})

            mark = (
                result
                .get("results", {})
                .get(subject, {})
                .get("total", 0)
            )

            scores.append(mark)

        if scores:

            subject_statistics[subject] = {

                "highest": max(scores),

                "lowest": min(scores),

                "average": round(sum(scores) / len(scores), 2),

                "pass": len([x for x in scores if x >= 50]),

                "fail": len([x for x in scores if x < 50])

            }

        else:

            subject_statistics[subject] = {

                "highest": 0,

                "lowest": 0,

                "average": 0,

                "pass": 0,

                "fail": 0

            }
    # =====================================================
    # RENDER PAGE
    # =====================================================

    return render_template(

    "broadsheet.html",

    school=school,

    students=students,

    subjects=subjects,

    sessions=sorted(results_collection.distinct("session")),

    classes=sorted(students_collection.distinct("class")),

    session=session,

    term=term,

    selected_class=selected_class,
    subject_statistics=subject_statistics,
    subject_short_names=subject_short_names

    )

if __name__ == "__main__":

    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000
    )