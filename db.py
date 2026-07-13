"""COMPASS — قاعدة البيانات (SQLite) + التهيئة والبيانات التجريبية."""
import sqlite3
import os
from werkzeug.security import generate_password_hash

# DB location — override with DB_PATH env var (e.g. a Render persistent disk) for durable data.
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "compass.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK(role IN ('student','advisor','admin'))
);

CREATE TABLE IF NOT EXISTS students (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL UNIQUE REFERENCES users(id),
    university_id     TEXT NOT NULL UNIQUE,
    level             INTEGER NOT NULL,
    track             TEXT,
    advisor_id        INTEGER REFERENCES users(id),
    admission_semester TEXT
);

CREATE TABLE IF NOT EXISTS courses (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    code              TEXT NOT NULL UNIQUE,
    name              TEXT NOT NULL,
    type              TEXT NOT NULL CHECK(type IN ('core','elective','free')),
    credits           INTEGER NOT NULL DEFAULT 3,
    parity            TEXT NOT NULL DEFAULT 'both' CHECK(parity IN ('odd','even','both')),
    recommended_level INTEGER,
    prereq            TEXT DEFAULT '',
    is_active         INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS semesters (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    is_active   INTEGER NOT NULL DEFAULT 0,
    wishes_open INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS wishes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER NOT NULL REFERENCES students(id),
    course_id   INTEGER NOT NULL REFERENCES courses(id),
    semester_id INTEGER NOT NULL REFERENCES semesters(id),
    status      TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
    advisor_note TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id, semester_id)
);

CREATE TABLE IF NOT EXISTS completed_courses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    name       TEXT NOT NULL,
    type       TEXT NOT NULL CHECK(type IN ('core','elective','free')),
    credits    INTEGER NOT NULL DEFAULT 3,
    grade      TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- طلبات عامة (مشروع التخرج، شهادة المسار، ... مستقبلاً) — كلها تعتمدها المرشدة
CREATE TABLE IF NOT EXISTS requests (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   INTEGER NOT NULL REFERENCES students(id),
    type         TEXT NOT NULL,
    title        TEXT NOT NULL,
    details      TEXT,
    eligible     INTEGER,
    status       TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
    advisor_note TEXT,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

-- البلوكات الجاهزة (يديرها المسؤول) — لكل مجموعة مستوى
CREATE TABLE IF NOT EXISTS blocks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    level_group TEXT NOT NULL,
    name        TEXT NOT NULL,
    courses     TEXT NOT NULL,
    is_active   INTEGER NOT NULL DEFAULT 1
);

-- فرق مشروع التخرج (بيانات منظّمة للداشبورد + Excel)
CREATE TABLE IF NOT EXISTS sp_teams (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id          INTEGER REFERENCES requests(id),
    student_id          INTEGER NOT NULL REFERENCES students(id),
    m1_name TEXT, m1_id TEXT, m1_email TEXT,
    m2_name TEXT, m2_id TEXT, m2_email TEXT,
    m3_name TEXT, m3_id TEXT, m3_email TEXT,
    phone               TEXT,
    supervisor_email    TEXT,
    supervisor_approved INTEGER DEFAULT 0,
    comments            TEXT,
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(force=False):
    if force and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = get_db()
    conn.executescript(SCHEMA)
    # ترحيل: عمود فصل التخرج في جدول الطلبات (لإفادة مطابقة الخطة)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(requests)").fetchall()]
    if "grad_semester" not in cols:
        conn.execute("ALTER TABLE requests ADD COLUMN grad_semester TEXT")
    if "block_id" not in cols:
        conn.execute("ALTER TABLE requests ADD COLUMN block_id INTEGER")
    conn.commit()
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        seed(conn)
    # seed blocks from the plan if the table is empty (first run or after adding the table)
    if conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0] == 0:
        from plan_data import BLOCKS
        for group, blist in BLOCKS.items():
            for b in blist:
                conn.execute("INSERT INTO blocks(level_group,name,courses,is_active) VALUES(?,?,?,1)",
                             (group, b["name"], ", ".join(b["courses"])))
        conn.commit()
    conn.close()


def seed(conn):
    c = conn.cursor()

    # إعدادات شروط التخرج
    reqs = {"core_credits": "121", "elective_courses": "9", "free_credits": "10"}
    for k, v in reqs.items():
        c.execute("INSERT INTO settings(key,value) VALUES(?,?)", (k, v))

    # المسؤول
    c.execute(
        "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
        ("Department Coordinator", "admin@compass.edu", generate_password_hash("admin123"), "admin"),
    )

    # المرشدات
    advisors = [
        ("Dr. Somayah Albaradei", "somayah@compass.edu"),
        ("Dr. Noura Alotaibi", "noura@compass.edu"),
    ]
    advisor_ids = []
    for name, email in advisors:
        c.execute(
            "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
            (name, email, generate_password_hash("advisor123"), "advisor"),
        )
        advisor_ids.append(c.lastrowid)

    # المقررات — الخطة الدراسية المعتمدة لقسم Computer Science (جامعة الملك عبدالعزيز)
    # الفصول 3–10 (السنوات 2–5) كما في دليل القسم، مع المتطلبات السابقة.
    # (code, name, type, credits, parity, recommended_level, prereq)
    courses = [
        # --- متطلبات سابقة من السنة التحضيرية (لصحة السلاسل) ---
        ("MATH-110", "Calculus (I)", "core", 3, "both", 2, ""),
        ("STAT-110", "Introduction to Statistics", "core", 3, "both", 2, ""),
        # --- الفصل الثالث (Total 13) ---
        ("CPIT-201", "Introduction to Computing", "core", 3, "odd", 3, ""),
        ("STAT-210", "Introduction to Computing Statistics", "core", 3, "odd", 3, "STAT-110"),
        ("CPIT-221", "Technical Writing", "core", 2, "odd", 3, ""),
        ("CPCS-202", "Programming (I)", "core", 3, "odd", 3, ""),
        ("ISLS-101", "Islamic Culture (I)", "core", 2, "odd", 3, ""),
        # --- الفصل الرابع (Total 14) ---
        ("CPCS-203", "Programming (II)", "core", 3, "even", 4, "CPCS-202"),
        ("CPCS-222", "Discrete Structures (I)", "core", 3, "even", 4, ""),
        ("MATH-202", "Calculus (II)", "core", 3, "even", 4, "MATH-110"),
        ("ARAB-101", "Language Skills", "core", 3, "even", 4, ""),
        ("ISLS-201", "Islamic Culture (II)", "core", 2, "even", 4, "ISLS-101"),
        # --- الفصل الخامس (Total 14) ---
        ("CPCS-204", "Data Structures (I)", "core", 3, "odd", 5, "CPCS-203"),
        ("CPCS-211", "Digital Logic Design", "core", 3, "odd", 5, "CPIT-201"),
        ("CPCS-212", "Applied Math for Computing (I)", "core", 4, "odd", 5, "MATH-202"),
        ("SCIE-100", "Lab Science (Physics/Biology/Chemistry)", "core", 4, "odd", 5, ""),
        # --- الفصل السادس (Total 15) ---
        ("CPCS-214", "Computer Organization & Architecture (I)", "core", 3, "even", 6, "CPCS-211"),
        ("CPCS-223", "Analysis & Design of Algorithms", "core", 3, "even", 6, "CPCS-204"),
        ("CPCS-241", "Database (I)", "core", 3, "even", 6, "CPCS-204"),
        ("STAT-352", "Applied Probability & Random Processes", "core", 3, "even", 6, "STAT-210"),
        ("CPCS-301", "Programming Languages", "core", 3, "even", 6, "CPCS-204, CPCS-222"),
        # --- الفصل السابع (Total 17) ---
        ("CPIS-334", "Software Project Management", "core", 2, "odd", 7, ""),
        ("CPCS-324", "Algorithms & Data Structures (II)", "core", 3, "odd", 7, "CPCS-222, CPCS-223"),
        ("CPCS-351", "Software Engineering (I)", "core", 3, "odd", 7, "CPCS-204"),
        ("CPCS-331", "Artificial Intelligence (I)", "core", 3, "odd", 7, "CPCS-204, CPCS-223"),
        ("CPCS-361", "Operating Systems (I)", "core", 3, "odd", 7, "CPCS-204, CPCS-214"),
        ("CPCS-371", "Computer Networks (I)", "core", 3, "odd", 7, "CPCS-214"),
        # --- الفصل الثامن (Total 13) ---
        ("CPCS-302", "Compiler Construction", "core", 3, "even", 8, "CPCS-301"),
        ("CPCS-381", "Human-Computer Interaction (I)", "core", 2, "even", 8, "CPCS-204"),
        ("ISLS-301", "Islamic Culture (III)", "core", 2, "even", 8, "ISLS-201"),
        ("CPCS-391", "Computer Graphics (I)", "core", 3, "even", 8, "CPCS-204, CPCS-212"),
        ("FREE-101", "College Free Course (I)", "free", 3, "both", 8, ""),
        # --- الفصل الصيفي ---
        ("CPCS-323", "Summer Training (200 hours)", "core", 0, "both", 8, "Department Approval"),
        # --- الفصل التاسع (Total 13) ---
        ("ARAB-201", "Writing Skills", "core", 3, "odd", 9, "ARAB-101"),
        ("CPCS-498", "Senior Project (I)", "core", 1, "odd", 9, "Senior Level"),
        ("DEPT-ELV-1", "Department Elective (I)", "elective", 3, "both", 9, ""),
        ("FREE-102", "College Free Course (II)", "free", 3, "both", 9, ""),
        ("FREE-103", "College Free Course (III)", "free", 3, "both", 9, ""),
        # --- الفصل العاشر (Total 13) ---
        ("ISLS-401", "Islamic Culture (IV)", "core", 2, "even", 10, "ISLS-301"),
        ("CPCS-499", "Senior Project (II)", "core", 3, "even", 10, "CPCS-498"),
        ("DEPT-ELV-2", "Department Elective (II)", "elective", 3, "both", 10, ""),
        ("CPIS-428", "Professional Computing Issues", "core", 3, "even", 10, "CPCS-323"),
        ("DEPT-ELV-3", "Department Elective (III)", "elective", 2, "both", 10, ""),
    ]
    for code, name, typ, cr, par, lvl, prereq in courses:
        c.execute(
            "INSERT INTO courses(code,name,type,credits,parity,recommended_level,prereq) VALUES(?,?,?,?,?,?,?)",
            (code, name, typ, cr, par, lvl, prereq),
        )

    # الفصل الدراسي القادم (تجميع الرغبات مفتوح)
    c.execute("INSERT INTO semesters(name,is_active,wishes_open) VALUES(?,?,?)",
              ("First Semester 2026", 1, 1))
    sem_id = c.lastrowid

    # Students — track is NULL (undeclared): all are at/below level 8, before the
    # department-elective stage (levels 9-10). Track is derived once they declare it
    # through their elective/track courses (Track Certificate).
    students = [
        # (name, email, university_id, level, track, advisor_index, admission)
        ("Sara Ahmed", "sara@compass.edu", "2110001", 4, None, 0, "1441"),
        ("Lama Mohammed", "lama@compass.edu", "2110002", 4, None, 0, "1441"),
        ("Reem Khaled", "reem@compass.edu", "2110003", 6, None, 0, "1439"),
        ("Jood Saad", "jood@compass.edu", "2110004", 6, None, 1, "1439"),
        ("Dana Fahad", "dana@compass.edu", "2110005", 8, None, 0, "1437"),
        ("Muneera Ali", "muneera@compass.edu", "2110006", 8, None, 1, "1437"),
    ]
    student_ids = []
    for name, email, uid, level, track, adv_i, adm in students:
        c.execute(
            "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
            (name, email, generate_password_hash("student123"), "student"),
        )
        u_id = c.lastrowid
        c.execute(
            "INSERT INTO students(user_id,university_id,level,track,advisor_id,admission_semester) VALUES(?,?,?,?,?,?)",
            (u_id, uid, level, track, advisor_ids[adv_i], adm),
        )
        student_ids.append(c.lastrowid)

    # سجل مكتمل تقريبي للطالبة المتوقع تخرجها (دانة، المستوى 8)
    grad_student = student_ids[4]
    for i in range(12):  # مواد أساسية
        c.execute("INSERT INTO completed_courses(student_id,name,type,credits,grade) VALUES(?,?,?,?,?)",
                  (grad_student, f"Core course {i+1}", "core", 9 if i == 11 else 10, "A"))
    for i in range(8):  # مواد اختيارية
        c.execute("INSERT INTO completed_courses(student_id,name,type,credits,grade) VALUES(?,?,?,?,?)",
                  (grad_student, f"Elective course {i+1}", "elective", 3, "B"))
    for i in range(3):  # مواد حرة
        c.execute("INSERT INTO completed_courses(student_id,name,type,credits,grade) VALUES(?,?,?,?,?)",
                  (grad_student, f"Free course {i+1}", "free", 3, "A"))

    # بعض الرغبات المبدئية لعرض الإحصائيات
    sample_wishes = [
        (student_ids[0], "CPCS-204", "pending"),
        (student_ids[0], "CPCS-211", "approved"),
        (student_ids[1], "CPCS-204", "approved"),
        (student_ids[1], "CPCS-211", "pending"),
        (student_ids[2], "CPCS-241", "approved"),
        (student_ids[2], "CPCS-223", "pending"),
        (student_ids[3], "CPCS-301", "pending"),
        (student_ids[4], "CPCS-499", "approved"),
        (student_ids[5], "CPCS-499", "pending"),
        (student_ids[5], "CPCS-391", "pending"),
    ]
    for sid, code, status in sample_wishes:
        cid = c.execute("SELECT id FROM courses WHERE code=?", (code,)).fetchone()[0]
        c.execute(
            "INSERT INTO wishes(student_id,course_id,semester_id,status) VALUES(?,?,?,?)",
            (sid, cid, sem_id, status),
        )

    conn.commit()


if __name__ == "__main__":
    init_db(force=True)
    print("COMPASS database initialized with demo data.")
    print("\nDemo accounts (password in parentheses):")
    print("  Admin:    admin@compass.edu       (admin123)")
    print("  Advisor:    somayah@compass.edu     (advisor123)")
    print("  Advisor:    noura@compass.edu       (advisor123)")
    print("  Student:    sara@compass.edu        (student123)")
    print("  Student:    dana@compass.edu        (student123)  <- expected graduate")
