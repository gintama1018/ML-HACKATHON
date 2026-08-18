import os
import sys
import urllib.parse
from datetime import datetime, timezone, date, timedelta
import random

# Ensure backend directory is in path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Password with proper URL encoding
raw_pw = "V$AM$RT8J$57he!"
enc_pw = urllib.parse.quote_plus(raw_pw)
user = "postgres.eskgeukkkllczotrowtj"

# Supabase Session Pooler (port 6543)
SUPABASE_URL = f"postgresql://{user}:{enc_pw}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

print(f"Connecting to Supabase PostgreSQL at aws-0-ap-southeast-1.pooler.supabase.com:6543...")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import (
    Base, User, Student, ParentStudentLink, TeacherClassLink,
    Attendance, Conversation, Message, Escalation, AuditLog,
    UserRole, AttendanceStatus, EscalationTarget, EscalationStatus
)
from src.auth.auth_service import hash_password

engine = create_engine(SUPABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_supabase():
    print("Creating all database tables in Supabase...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    db = SessionLocal()
    try:
        default_pwd = hash_password("School@123")
        
        print("Seeding Principal...")
        principal = User(
            id="usr-principal-01",
            name="Dr. Sunita Sharma",
            email="principal@xyzschool.edu",
            phone="+919876543210",
            role=UserRole.PRINCIPAL.value,
            password_hash=default_pwd,
            language_pref="en",
            is_verified=True
        )
        db.add(principal)
        
        print("Seeding Teachers...")
        teachers_data = [
            {"id": "usr-teacher-10a", "name": "Amit Verma", "email": "amit.verma@xyzschool.edu", "phone": "+919811100001", "class": "10", "section": "A", "subject": "Mathematics", "lang": "en"},
            {"id": "usr-teacher-10b", "name": "Meenakshi Sundaram", "email": "meenakshi.s@xyzschool.edu", "phone": "+919811100002", "class": "10", "section": "B", "subject": "Science", "lang": "ta"},
            {"id": "usr-teacher-9a", "name": "Rajeshwari Iyer", "email": "rajeshwari.i@xyzschool.edu", "phone": "+919811100003", "class": "9", "section": "A", "subject": "English", "lang": "en"},
            {"id": "usr-teacher-9b", "name": "Vikram Sengupta", "email": "vikram.s@xyzschool.edu", "phone": "+919811100004", "class": "9", "section": "B", "subject": "Social Studies", "lang": "bn"},
            {"id": "usr-teacher-8a", "name": "Anita Desai", "email": "anita.d@xyzschool.edu", "phone": "+919811100005", "class": "8", "section": "A", "subject": "Hindi", "lang": "hi"},
        ]
        
        teachers_by_class = {}
        for t in teachers_data:
            user = User(
                id=t["id"],
                name=t["name"],
                email=t["email"],
                phone=t["phone"],
                role=UserRole.TEACHER.value,
                password_hash=default_pwd,
                language_pref=t["lang"],
                is_verified=True
            )
            db.add(user)
            db.flush()
            
            link = TeacherClassLink(
                id=f"tcl-{t['class']}{t['section']}",
                teacher_id=user.id,
                class_name=t["class"],
                section=t["section"],
                subject=t["subject"]
            )
            db.add(link)
            teachers_by_class[f"{t['class']}-{t['section']}"] = user.id

        print("Seeding Students and Profiles...")
        students_meta = [
            # Class 10-A
            {"uid": "usr-stu-101", "sid": "stu-101", "name": "Aarav Sharma", "email": "aarav.sharma@xyzschool.edu", "class": "10", "section": "A", "roll": "101", "contact": "+919822200001", "parent_email": "rajesh.parent@xyzschool.edu"},
            {"uid": "usr-stu-102", "sid": "stu-102", "name": "Diya Patel", "email": "diya.patel@xyzschool.edu", "class": "10", "section": "A", "roll": "102", "contact": "+919822200002", "parent_email": "priya.parent@xyzschool.edu"},
            {"uid": "usr-stu-103", "sid": "stu-103", "name": "Rohan Mehta", "email": "rohan.mehta@xyzschool.edu", "class": "10", "section": "A", "roll": "103", "contact": "+919822200003", "parent_email": "suresh.parent@xyzschool.edu"},
            {"uid": "usr-stu-104", "sid": "stu-104", "name": "Ananya Gupta", "email": "ananya.gupta@xyzschool.edu", "class": "10", "section": "A", "roll": "104", "contact": "+919822200004", "parent_email": "sunita.parent@xyzschool.edu"},
            {"uid": "usr-stu-105", "sid": "stu-105", "name": "Siddharth Rao", "email": "siddharth.rao@xyzschool.edu", "class": "10", "section": "A", "roll": "105", "contact": "+919822200005", "parent_email": "ramesh.parent@xyzschool.edu"},
            
            # Class 10-B
            {"uid": "usr-stu-201", "sid": "stu-201", "name": "Ishaan Verma", "email": "ishaan.verma@xyzschool.edu", "class": "10", "section": "B", "roll": "201", "contact": "+919822200006", "parent_email": "mohan.parent@xyzschool.edu"},
            {"uid": "usr-stu-202", "sid": "stu-202", "name": "Tanvi Joshi", "email": "tanvi.joshi@xyzschool.edu", "class": "10", "section": "B", "roll": "202", "contact": "+919822200007", "parent_email": "geeta.parent@xyzschool.edu"},
            {"uid": "usr-stu-203", "sid": "stu-203", "name": "Aditya Kulkarni", "email": "aditya.kulkarni@xyzschool.edu", "class": "10", "section": "B", "roll": "203", "contact": "+919822200008", "parent_email": "anand.parent@xyzschool.edu"},
            {"uid": "usr-stu-204", "sid": "stu-204", "name": "Riya Nair", "email": "riya.nair@xyzschool.edu", "class": "10", "section": "B", "roll": "204", "contact": "+919822200009", "parent_email": "lakshmi.parent@xyzschool.edu"},
            {"uid": "usr-stu-205", "sid": "stu-205", "name": "Karan Singhania", "email": "karan.singhania@xyzschool.edu", "class": "10", "section": "B", "roll": "205", "contact": "+919822200010", "parent_email": "harish.parent@xyzschool.edu"},
            
            # Class 9-A
            {"uid": "usr-stu-301", "sid": "stu-301", "name": "Kabir Patel", "email": "kabir.patel@xyzschool.edu", "class": "9", "section": "A", "roll": "301", "contact": "+919822200011", "parent_email": "priya.parent@xyzschool.edu"},
            {"uid": "usr-stu-302", "sid": "stu-302", "name": "Sneha Reddy", "email": "sneha.reddy@xyzschool.edu", "class": "9", "section": "A", "roll": "302", "contact": "+919822200012", "parent_email": "venkat.parent@xyzschool.edu"},
            {"uid": "usr-stu-303", "sid": "stu-303", "name": "Manav Banerjee", "email": "manav.banerjee@xyzschool.edu", "class": "9", "section": "A", "roll": "303", "contact": "+919822200013", "parent_email": "subhash.parent@xyzschool.edu"},
            {"uid": "usr-stu-304", "sid": "stu-304", "name": "Pooja Hegde", "email": "pooja.hegde@xyzschool.edu", "class": "9", "section": "A", "roll": "304", "contact": "+919822200014", "parent_email": "srinivas.parent@xyzschool.edu"},
            {"uid": "usr-stu-305", "sid": "stu-305", "name": "Arjun Kapoor", "email": "arjun.kapoor@xyzschool.edu", "class": "9", "section": "A", "roll": "305", "contact": "+919822200015", "parent_email": "boney.parent@xyzschool.edu"},
            
            # Class 9-B
            {"uid": "usr-stu-401", "sid": "stu-401", "name": "Devansh Shah", "email": "devansh.shah@xyzschool.edu", "class": "9", "section": "B", "roll": "401", "contact": "+919822200016", "parent_email": "ashok.parent@xyzschool.edu"},
            {"uid": "usr-stu-402", "sid": "stu-402", "name": "Meera Nambiar", "email": "meera.nambiar@xyzschool.edu", "class": "9", "section": "B", "roll": "402", "contact": "+919822200017", "parent_email": "radha.parent@xyzschool.edu"},
            {"uid": "usr-stu-403", "sid": "stu-403", "name": "Yash Vardhan", "email": "yash.vardhan@xyzschool.edu", "class": "9", "section": "B", "roll": "403", "contact": "+919822200018", "parent_email": "kamal.parent@xyzschool.edu"},
            {"uid": "usr-stu-404", "sid": "stu-404", "name": "Kriti Sanon", "email": "kriti.sanon@xyzschool.edu", "class": "9", "section": "B", "roll": "404", "contact": "+919822200019", "parent_email": "rahul.sanon.parent@xyzschool.edu"},
            {"uid": "usr-stu-405", "sid": "stu-405", "name": "Neeraj Chopra", "email": "neeraj.chopra@xyzschool.edu", "class": "9", "section": "B", "roll": "405", "contact": "+919822200020", "parent_email": "satish.parent@xyzschool.edu"},
            
            # Class 8-A
            {"uid": "usr-stu-501", "sid": "stu-501", "name": "Ananya Sharma", "email": "ananya.sharma@xyzschool.edu", "class": "8", "section": "A", "roll": "501", "contact": "+919822200021", "parent_email": "rajesh.parent@xyzschool.edu"},
            {"uid": "usr-stu-502", "sid": "stu-502", "name": "Varun Dhawan", "email": "varun.dhawan@xyzschool.edu", "class": "8", "section": "A", "roll": "502", "contact": "+919822200022", "parent_email": "david.parent@xyzschool.edu"},
            {"uid": "usr-stu-503", "sid": "stu-503", "name": "Shraddha Kapoor", "email": "shraddha.kapoor@xyzschool.edu", "class": "8", "section": "A", "roll": "503", "contact": "+919822200023", "parent_email": "shakti.parent@xyzschool.edu"},
            {"uid": "usr-stu-504", "sid": "stu-504", "name": "Rahul Dravid Jr", "email": "rahul.dravid.jr@xyzschool.edu", "class": "8", "section": "A", "roll": "504", "contact": "+919822200024", "parent_email": "rahul.sr.parent@xyzschool.edu"},
            {"uid": "usr-stu-505", "sid": "stu-505", "name": "Sania Mirza Jr", "email": "sania.mirza.jr@xyzschool.edu", "class": "8", "section": "A", "roll": "505", "contact": "+919822200025", "parent_email": "imran.parent@xyzschool.edu"},
        ]
        
        student_obj_map = {}
        for s in students_meta:
            u = User(
                id=s["uid"],
                name=s["name"],
                email=s["email"],
                phone=s["contact"],
                role=UserRole.STUDENT.value,
                password_hash=default_pwd,
                language_pref="en",
                is_verified=True
            )
            db.add(u)
            db.flush()
            
            stu = Student(
                id=s["sid"],
                user_id=u.id,
                class_name=s["class"],
                section=s["section"],
                roll_no=s["roll"],
                emergency_contact=s["contact"]
            )
            db.add(stu)
            db.flush()
            student_obj_map[s["sid"]] = stu

        print("Seeding Parents and Links...")
        parents_data = [
            {"id": "usr-par-01", "name": "Rajesh Sharma", "email": "rajesh.parent@xyzschool.edu", "phone": "+919833300001", "lang": "hi", "kids": ["stu-101", "stu-501"]},
            {"id": "usr-par-02", "name": "Priya Patel", "email": "priya.parent@xyzschool.edu", "phone": "+919833300002", "lang": "en", "kids": ["stu-102", "stu-301"]},
            {"id": "usr-par-03", "name": "Suresh Mehta", "email": "suresh.parent@xyzschool.edu", "phone": "+919833300003", "lang": "en", "kids": ["stu-103"]},
            {"id": "usr-par-04", "name": "Sunita Gupta", "email": "sunita.parent@xyzschool.edu", "phone": "+919833300004", "lang": "en", "kids": ["stu-104"]},
            {"id": "usr-par-05", "name": "Ramesh Rao", "email": "ramesh.parent@xyzschool.edu", "phone": "+919833300005", "lang": "ta", "kids": ["stu-105"]},
            {"id": "usr-par-06", "name": "Mohan Verma", "email": "mohan.parent@xyzschool.edu", "phone": "+919833300006", "lang": "hi", "kids": ["stu-201"]},
            {"id": "usr-par-07", "name": "Geeta Joshi", "email": "geeta.parent@xyzschool.edu", "phone": "+919833300007", "lang": "en", "kids": ["stu-202"]},
            {"id": "usr-par-08", "name": "Anand Kulkarni", "email": "anand.parent@xyzschool.edu", "phone": "+919833300008", "lang": "en", "kids": ["stu-203"]},
            {"id": "usr-par-09", "name": "Lakshmi Nair", "email": "lakshmi.parent@xyzschool.edu", "phone": "+919833300009", "lang": "en", "kids": ["stu-204"]},
            {"id": "usr-par-10", "name": "Harish Singhania", "email": "harish.parent@xyzschool.edu", "phone": "+919833300010", "lang": "en", "kids": ["stu-205"]},
            {"id": "usr-par-11", "name": "Venkat Reddy", "email": "venkat.parent@xyzschool.edu", "phone": "+919833300011", "lang": "en", "kids": ["stu-302"]},
            {"id": "usr-par-12", "name": "Subhash Banerjee", "email": "subhash.parent@xyzschool.edu", "phone": "+919833300012", "lang": "bn", "kids": ["stu-303"]},
            {"id": "usr-par-13", "name": "Srinivas Hegde", "email": "srinivas.parent@xyzschool.edu", "phone": "+919833300013", "lang": "en", "kids": ["stu-304"]},
            {"id": "usr-par-14", "name": "Boney Kapoor", "email": "boney.parent@xyzschool.edu", "phone": "+919833300014", "lang": "hi", "kids": ["stu-305"]},
            {"id": "usr-par-15", "name": "Ashok Shah", "email": "ashok.parent@xyzschool.edu", "phone": "+919833300015", "lang": "en", "kids": ["stu-401"]},
            {"id": "usr-par-16", "name": "Radha Nambiar", "email": "radha.parent@xyzschool.edu", "phone": "+919833300016", "lang": "en", "kids": ["stu-402"]},
            {"id": "usr-par-17", "name": "Kamal Vardhan", "email": "kamal.parent@xyzschool.edu", "phone": "+919833300017", "lang": "en", "kids": ["stu-403"]},
            {"id": "usr-par-18", "name": "Rahul Sanon", "email": "rahul.sanon.parent@xyzschool.edu", "phone": "+919833300018", "lang": "en", "kids": ["stu-404"]},
            {"id": "usr-par-19", "name": "Satish Chopra", "email": "satish.parent@xyzschool.edu", "phone": "+919833300019", "lang": "hi", "kids": ["stu-405"]},
            {"id": "usr-par-20", "name": "David Dhawan", "email": "david.parent@xyzschool.edu", "phone": "+919833300020", "lang": "en", "kids": ["stu-502"]},
            {"id": "usr-par-21", "name": "Shakti Kapoor", "email": "shakti.parent@xyzschool.edu", "phone": "+919833300021", "lang": "hi", "kids": ["stu-503"]},
            {"id": "usr-par-22", "name": "Rahul Dravid Sr", "email": "rahul.sr.parent@xyzschool.edu", "phone": "+919833300022", "lang": "en", "kids": ["stu-504"]},
            {"id": "usr-par-23", "name": "Imran Mirza", "email": "imran.parent@xyzschool.edu", "phone": "+919833300023", "lang": "en", "kids": ["stu-505"]},
        ]
        
        for p in parents_data:
            user = User(
                id=p["id"],
                name=p["name"],
                email=p["email"],
                phone=p["phone"],
                role=UserRole.PARENT.value,
                password_hash=default_pwd,
                language_pref=p["lang"],
                is_verified=True
            )
            db.add(user)
            db.flush()
            
            for k_id in p["kids"]:
                link = ParentStudentLink(
                    id=f"psl-{user.id}-{k_id}",
                    parent_id=user.id,
                    student_id=k_id,
                    relationship_type="parent"
                )
                db.add(link)

        print("Seeding 30 Days Attendance History for all 25 students...")
        today = date.today()
        school_dates = []
        cur_date = today - timedelta(days=45)
        while len(school_dates) < 30 and cur_date <= today:
            if cur_date.weekday() < 5:
                school_dates.append(cur_date)
            cur_date += timedelta(days=1)
            
        random.seed(42)
        
        attendance_records = []
        for s in students_meta:
            s_class_key = f"{s['class']}-{s['section']}"
            marker_teacher_id = teachers_by_class[s_class_key]
            
            for d in school_dates:
                rnd = random.random()
                if rnd < 0.90:
                    st = AttendanceStatus.PRESENT.value
                    rmk = "On time"
                elif rnd < 0.96:
                    st = AttendanceStatus.ABSENT.value
                    rmk = "Unexcused absence"
                elif rnd < 0.99:
                    st = AttendanceStatus.LATE.value
                    rmk = "Late by 15 mins"
                else:
                    st = AttendanceStatus.EXCUSED.value
                    rmk = "Medical leave"
                
                marked_dt = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=8, minutes=30)
                
                att = Attendance(
                    id=f"att-{s['sid']}-{d.isoformat()}",
                    student_id=s["sid"],
                    date=d,
                    status=st,
                    marked_by=marker_teacher_id,
                    marked_at=marked_dt,
                    remarks=rmk
                )
                attendance_records.append(att)
                
        db.bulk_save_objects(attendance_records)
        
        print("Seeding Initial Audit Logs & System Init Record...")
        sample_audit = AuditLog(
            id="audit-init-01",
            user_id=principal.id,
            action="SYSTEM_INIT",
            resource="database",
            result="allowed",
            details="Seeded initial Supabase PostgreSQL database with 25 students, 5 teachers, 23 parents, 1 principal, 750 attendance records.",
            ip_address="127.0.0.1",
            timestamp=datetime.now(timezone.utc)
        )
        db.add(sample_audit)
        
        db.commit()
        print("\n=======================================================")
        print(">>> SUPABASE DATABASE SEEDING COMPLETED SUCCESSFULLY! <<<")
        print(f"Summary: 1 Principal, 5 Teachers, 25 Students, 23 Parents, {len(attendance_records)} Attendance records.")
        print("=======================================================\n")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding Supabase database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_supabase()
