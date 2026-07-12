"""إضافة حسابات المرشدات الأكاديميات الحقيقيات إلى COMPASS.

- يُدرج كل مرشدة كمستخدم بدور 'advisor' بكلمة مرور افتراضية.
- إيميلات مكرّرة (نفس البريد) تُدرج مرة واحدة فقط (email فريد في القاعدة).
- آمن للتشغيل أكثر من مرة: الموجود مسبقاً يُتخطّى.
"""
from db import get_db, init_db
from werkzeug.security import generate_password_hash

DEFAULT_PASSWORD = "advisor123"  # كلمة مرور افتراضية موحّدة — يُنصح بتغييرها لاحقاً

# (الاسم، البريد) — البريد يُخزَّن بأحرف صغيرة ليطابق تسجيل الدخول
ADVISORS = [
    ("الدكتورة آلاء بافيل", "aabafail@kau.edu.sa"),
    ("الأستاذة مي نصير", "mnassier@kau.edu.sa"),
    ("الأستاذة نجود الشهري", "nmhalshehri@kau.edu.sa"),
    ("الدكتورة رشا مرزا", "rmirza@kau.edu.sa"),
    ("الدكتورة روان الشيخ", "rsalshaikh@kau.edu.sa"),
    ("الأستاذة سعاد المعبدي", "salmabdy@kau.edu.sa"),
    ("الدكتورة هديل سروجي", "hsurouji@kau.edu.sa"),
    ("الدكتورة عبير الهذلي", "aalhathle@kau.edu.sa"),
    ("الأستاذة بسمة شعيب", "bshuaib@kau.edu.sa"),
    ("الدكتورة ناهد العويضي", "nalowidi@kau.edu.sa"),
    ("الدكتورة ندى باجنيد", "nbajnaid@kau.edu.sa"),
    ("الدكتورة إيمان الحربي", "ealraddadi@kau.edu.sa"),
    ("الأستاذة تهاني المشدق", "tsalmoshadak@kau.edu.sa"),
    ("الأستاذة أسماء الشنقيطي", "aalshenkity@kau.edu.sa"),
    ("الدكتورة هدى الجلعود", "haljalaoud@kau.edu.sa"),
    ("الدكتورة أمل المنصور", "aalmansour@kau.edu.sa"),
    ("الأستاذة سارة الحسن", "ssmalhasan8@kau.edu.sa"),
    ("الدكتورة سمية البرادعي", "salbaradei@kau.edu.sa"),
    ("الدكتورة هيلين بخش", "hbakhsh@kau.edu.sa"),
    ("الدكتورة لولوة الحريقي", "lalharigy@kau.edu.sa"),
    ("الدكتورة نوف أبوخضير", "nabukhodair@kau.edu.sa"),
    ("الدكتورة كوثر موريا", "kmoria@kau.edu.sa"),
    ("الدكتورة هدى الغامدي", "hdalgamdi@kau.edu.sa"),
    ("الدكتورة مي فاضل", "mfadel@kau.edu.sa"),
    ("الدكتورة أروى باصبرين", "abasabreen@kau.edu.sa"),
    ("الدكتورة منى الشهري", "msalshehri@kau.edu.sa"),
    ("الدكتورة علا الصاعدي", "oaalsaedi@kau.edu.sa"),
    ("الدكتورة سارة ساعد النفيعي", "salnefaie@kau.edu.sa"),
]


def run():
    init_db()  # يضمن وجود القاعدة والجداول
    db = get_db()
    added, skipped = [], []
    seen = set()
    for name, email in ADVISORS:
        email = email.strip().lower()
        if email in seen:
            continue
        seen.add(email)
        exists = db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone()
        if exists:
            skipped.append((name, email))
            continue
        db.execute(
            "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,'advisor')",
            (name, email, generate_password_hash(DEFAULT_PASSWORD)),
        )
        added.append((name, email))
    db.commit()

    total = db.execute("SELECT COUNT(*) FROM users WHERE role='advisor'").fetchone()[0]
    print(f"تمت الإضافة: {len(added)} | مُتخطّاة (موجودة مسبقاً): {len(skipped)}")
    print(f"إجمالي المرشدات الآن في النظام: {total}")
    print(f"كلمة المرور الافتراضية للجميع: {DEFAULT_PASSWORD}\n")
    if added:
        print("الحسابات المُضافة:")
        for name, email in added:
            print(f"  • {name:<28} {email}")
    if skipped:
        print("\nمُتخطّاة (كانت موجودة):")
        for name, email in skipped:
            print(f"  • {name:<28} {email}")


if __name__ == "__main__":
    run()
