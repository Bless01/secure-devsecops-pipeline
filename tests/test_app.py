import secrets

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db, init_db


@pytest.fixture()
def app(tmp_path):
    """Create an application with a separate test database."""
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": secrets.token_hex(32),
            "DATABASE": str(tmp_path / "test.sqlite"),
        }
    )

    passwords = {
        "BU2026001": secrets.token_urlsafe(18),
        "BU2026002": secrets.token_urlsafe(18),
    }
    test_app.config["TEST_PASSWORDS"] = passwords

    with test_app.app_context():
        init_db()
        db = get_db()

        students = [
            (
                1,
                "BU2026001",
                "Linda Mpumulo",
                "linda.mpumulo@blessings.example",
                "Linda profile biography.",
                94,
                "A",
            ),
            (
                2,
                "BU2026002",
                "Daniel Banda",
                "daniel.banda@blessings.example",
                "Daniel profile biography.",
                85,
                "B",
            ),
        ]

        db.execute(
            """
            INSERT INTO courses (id, course_code, title, credits)
            VALUES (?, ?, ?, ?)
            """,
            (1, "CIS 693", "Cybersecurity Capstone Project", 3),
        )

        for student_id, number, name, email, biography, score, grade in students:
            db.execute(
                """
                INSERT INTO students (
                    id, student_number, full_name, email,
                    password_hash, program, academic_level, biography
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    number,
                    name,
                    email,
                    generate_password_hash(passwords[number]),
                    "Master of Science in Cybersecurity",
                    "Graduate Student",
                    biography,
                ),
            )

            db.execute(
                """
                INSERT INTO enrollments (
                    id, student_id, course_id, semester
                )
                VALUES (?, ?, ?, ?)
                """,
                (student_id, student_id, 1, "Fall 2026"),
            )

            db.execute(
                """
                INSERT INTO grades (enrollment_id, score, letter_grade)
                VALUES (?, ?, ?)
                """,
                (student_id, score, grade),
            )

        db.commit()

    yield test_app


@pytest.fixture()
def client(app):
    """Create a browser-like client for requests."""
    return app.test_client()


@pytest.fixture()
def login(client, app):
    """Provide a helper that signs in through the login form."""
    def sign_in(student_number="BU2026001", username=None):
        return client.post(
            "/login",
            data={
                "username": username or student_number,
                "password": app.config["TEST_PASSWORDS"][student_number],
            },
        )

    return sign_in


def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Blessings University" in response.data


def test_login_page(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Student Login" in response.data


@pytest.mark.parametrize(
    "student_number, student_id",
    [
        ("BU2026001", 1),
        ("BU2026002", 2),
    ],
)
def test_valid_login(client, login, student_number, student_id):
    response = login(student_number)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    with client.session_transaction() as session:
        assert session["student_id"] == student_id


def test_login_with_email(client, login):
    response = login(
        username="linda.mpumulo@blessings.example"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    with client.session_transaction() as session:
        assert session["student_id"] == 1


@pytest.mark.parametrize(
    "username, password",
    [
        ("BU2026001", "incorrect-password"),
        ("UNKNOWN-STUDENT", "incorrect-password"),
        ("", ""),
    ],
)
def test_invalid_login(client, username, password):
    response = client.post(
        "/login",
        data={"username": username, "password": password},
    )

    assert response.status_code == 200
    assert b"Invalid student ID, email, or password." in response.data

    with client.session_transaction() as session:
        assert "student_id" not in session

    protected_response = client.get("/dashboard")
    assert protected_response.status_code == 302
    assert protected_response.headers["Location"].endswith("/login")


@pytest.mark.parametrize(
    "path",
    ["/dashboard", "/grades", "/profile"],
)
def test_pages_require_login(client, path):
    response = client.get(path)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


@pytest.mark.parametrize(
    "student_number, name, other_name",
    [
        ("BU2026001", "Linda", "Daniel"),
        ("BU2026002", "Daniel", "Linda"),
    ],
)
def test_dashboard_shows_current_student(
    client, login, student_number, name, other_name
):
    login(student_number)
    response = client.get("/dashboard")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f"Welcome, {name}" in page
    assert student_number in page
    assert f"Welcome, {other_name}" not in page


@pytest.mark.parametrize(
    "student_number, name, score, other_name, other_score",
    [
        ("BU2026001", "Linda Mpumulo", "94.0%", "Daniel Banda", "85.0%"),
        ("BU2026002", "Daniel Banda", "85.0%", "Linda Mpumulo", "94.0%"),
    ],
)
def test_grades_show_only_current_student(
    client, login, student_number, name, score, other_name, other_score
):
    login(student_number)
    response = client.get("/grades")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert name in page
    assert student_number in page
    assert "CIS 693" in page
    assert score in page
    assert other_name not in page
    assert other_score not in page


@pytest.mark.parametrize(
    "student_number, name, biography, other_name, other_biography",
    [
        (
            "BU2026001",
            "Linda Mpumulo",
            "Linda profile biography.",
            "Daniel Banda",
            "Daniel profile biography.",
        ),
        (
            "BU2026002",
            "Daniel Banda",
            "Daniel profile biography.",
            "Linda Mpumulo",
            "Linda profile biography.",
        ),
    ],
)
def test_profile_shows_only_current_student(
    client, login, student_number, name,
    biography, other_name, other_biography
):
    login(student_number)
    response = client.get("/profile")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert name in page
    assert student_number in page
    assert biography in page
    assert other_name not in page
    assert other_biography not in page


@pytest.mark.parametrize(
    "path, own_record, other_record",
    [
        ("/grades", "94.0%", "85.0%"),
        (
            "/profile",
            "Linda profile biography.",
            "Daniel profile biography.",
        ),
    ],
)
def test_url_parameter_cannot_switch_student(
    client, login, path, own_record, other_record
):
    login("BU2026001")

    response = client.get(
        path,
        query_string={"student_id": 2},
    )
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert own_record in page
    assert other_record not in page


def test_logout_ends_session(client, login):
    login()
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    with client.session_transaction() as session:
        assert "student_id" not in session

    for path in ("/dashboard", "/grades", "/profile"):
        response = client.get(path)

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}