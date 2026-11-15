from getpass import getpass

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db


def seed_database():
    """Add fictional records without replacing existing records."""
    app = create_app()

    students = [
        (
            "BU2026001",
            "Linda Mpumulo",
            "linda.mpumulo@blessings.example",
        ),
        (
            "BU2026002",
            "Daniel Banda",
            "daniel.banda@blessings.example",
        ),
    ]

    courses = [
        ("CIS 693", "Cybersecurity Capstone Project", 3),
        ("CIS 620", "Secure Software Engineering", 3),
        ("CIS 635", "Computer Network Security", 3),
    ]

    results = {
        "BU2026001": [(94, "A"), (91, "A-"), (88, "B+")],
        "BU2026002": [(85, "B"), (88, "B+"), (92, "A-")],
    }

    with app.app_context():
        db = get_db()

        with db:
            for code, title, credits in courses:
                db.execute(
                    """
                    INSERT INTO courses (course_code, title, credits)
                    VALUES (?, ?, ?)
                    ON CONFLICT(course_code) DO NOTHING
                    """,
                    (code, title, credits),
                )

            for number, name, email in students:
                student = db.execute(
                    "SELECT id FROM students WHERE student_number = ?",
                    (number,),
                ).fetchone()

                if student is None:
                    print(f"\nCreate an account for {name} ({number}).")

                    while True:
                        password = getpass("Choose a password (12+ characters): ")
                        confirmation = getpass("Confirm password: ")

                        if len(password) < 12:
                            print("Please use at least 12 characters.")
                        elif password != confirmation:
                            print("Passwords do not match. Try again.")
                        else:
                            break

                    cursor = db.execute(
                        """
                        INSERT INTO students (
                            student_number, full_name, email,
                            password_hash, program, academic_level
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            number,
                            name,
                            email,
                            generate_password_hash(password),
                            "Master of Science in Cybersecurity",
                            "Graduate Student",
                        ),
                    )
                    student_id = cursor.lastrowid
                else:
                    student_id = student["id"]
                    print(f"{name}: keeping the existing account.")

                for course, result in zip(courses, results[number]):
                    course_id = db.execute(
                        "SELECT id FROM courses WHERE course_code = ?",
                        (course[0],),
                    ).fetchone()["id"]

                    db.execute(
                        """
                        INSERT INTO enrollments (
                            student_id, course_id, semester
                        )
                        VALUES (?, ?, ?)
                        ON CONFLICT(student_id, course_id, semester)
                        DO NOTHING
                        """,
                        (student_id, course_id, "Fall 2026"),
                    )

                    enrollment_id = db.execute(
                        """
                        SELECT id FROM enrollments
                        WHERE student_id = ?
                          AND course_id = ?
                          AND semester = ?
                        """,
                        (student_id, course_id, "Fall 2026"),
                    ).fetchone()["id"]

                    db.execute(
                        """
                        INSERT INTO grades (
                            enrollment_id, score, letter_grade
                        )
                        VALUES (?, ?, ?)
                        ON CONFLICT(enrollment_id) DO NOTHING
                        """,
                        (enrollment_id, result[0], result[1]),
                    )

        print("\nStudent accounts, courses, and grades added successfully.")


if __name__ == "__main__":
    seed_database()