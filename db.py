# =========================================
# db.py
# STELLA MARIS COLLEGE PORTAL DATABASE
# =========================================

from pymongo import MongoClient
from pymongo.errors import (
    ServerSelectionTimeoutError,
    ConnectionFailure
)

from dotenv import load_dotenv

import os
import time

# =========================================
# LOAD ENV VARIABLES
# =========================================

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# =========================================
# GLOBAL VARIABLES
# =========================================

client = None
db = None

students_collection = None
admins_collection = None
classes_collection = None
results_collection = None

settings_collection = None
teachers_collection = None
subjects_collection = None
attendance_collection = None
parents_collection = None

USE_MONGODB = False

# =========================================
# RETRY SETTINGS
# =========================================

MAX_RETRIES = 3
RETRY_DELAY = 2

# =========================================
# CONNECT TO MONGODB
# =========================================

def connect_mongo():

    global client
    global db

    global students_collection
    global admins_collection
    global classes_collection
    global results_collection

    global settings_collection
    global teachers_collection
    global subjects_collection
    global attendance_collection
    global parents_collection

    global USE_MONGODB

    if not MONGO_URI:

        print("\n❌ ERROR: MONGO_URI not found")

        USE_MONGODB = False

        return False

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            print("\n🔄 Connecting to MongoDB...")
            print(f"📡 Attempt {attempt}/{MAX_RETRIES}")

            client = MongoClient(

                MONGO_URI,

                serverSelectionTimeoutMS=5000

            )

            client.admin.command("ping")

            db = client["school_portal"]

            # =====================================
            # COLLECTIONS
            # =====================================

            students_collection = db["students"]

            admins_collection = db["admins"]

            classes_collection = db["classes"]

            results_collection = db["results"]

            settings_collection = db["settings"]

            teachers_collection = db["teachers"]

            subjects_collection = db["subjects"]

            attendance_collection = db["attendance"]

            parents_collection = db["parents"]

            # =====================================
            # INDEXES
            # =====================================

            students_collection.create_index(

                "student_id",

                unique=True

            )

            admins_collection.create_index(

                "username",

                unique=True

            )

            classes_collection.create_index(

                "name",

                unique=True

            )

            teachers_collection.create_index(

                "teacher_id",

                unique=True

            )

            subjects_collection.create_index(

                "subject_name",

                unique=True

            )

            USE_MONGODB = True

            print("\n✅ MongoDB Connected Successfully")

            print("✅ Database Ready")

            print("✅ Collections Ready")

            return True

        except ServerSelectionTimeoutError as e:

            print("\n❌ MongoDB Connection Failed")

            print(e)

        except ConnectionFailure as e:

            print("\n❌ MongoDB Connection Failure")

            print(e)

        except Exception as e:

            print("\n❌ Unexpected MongoDB Error")

            print(e)

        print(f"\n⏳ Retrying in {RETRY_DELAY} seconds...\n")

        time.sleep(RETRY_DELAY)

    USE_MONGODB = False

    students_collection = None
    admins_collection = None
    classes_collection = None
    results_collection = None

    settings_collection = None
    teachers_collection = None
    subjects_collection = None
    attendance_collection = None
    parents_collection = None

    print("""
=========================================
⚠️ MONGODB CONNECTION FAILED
=========================================

Your Flask app can still run.

BUT:

❌ Data will not save permanently
❌ Login data may not persist
❌ Results may reset after restart

=========================================
""")

    return False

# =========================================
# INITIALIZE CONNECTION
# =========================================

connected = connect_mongo()

# =========================================
# EXPORT VARIABLES
# =========================================

__all__ = [

    "client",

    "db",

    "students_collection",

    "admins_collection",

    "classes_collection",

    "results_collection",

    "settings_collection",

    "teachers_collection",

    "subjects_collection",

    "attendance_collection",

    "parents_collection",

    "USE_MONGODB",

    "connected"

]