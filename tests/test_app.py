import pytest

from app import create_app


@pytest.fixture()
def client():
    """Create a test client for the Flask application."""
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def test_home_page(client):
    """Confirm that the university homepage loads successfully."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"Blessings University Student Portal" in response.data


def test_login_page(client):
    """Confirm that the student login page loads successfully."""
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Student Login" in response.data


def test_login_redirects_to_dashboard(client):
    """Confirm that submitting the visual login opens the dashboard."""
    response = client.post(
        "/login",
        data={
            "username": "BU2026001",
            "password": "Student123!",
        },
    )

    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


def test_dashboard_page(client):
    """Confirm that the student dashboard loads successfully."""
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Welcome, Linda" in response.data


def test_grades_page(client):
    """Confirm that the student grades page loads successfully."""
    response = client.get("/grades")

    assert response.status_code == 200
    assert b"Student Grades" in response.data
    assert b"Linda Mpumulo" in response.data


def test_profile_page(client):
    """Confirm that the student profile page loads successfully."""
    response = client.get("/profile")

    assert response.status_code == 200
    assert b"Student Profile" in response.data
    assert b"Linda Mpumulo" in response.data


def test_logout_redirects_to_home(client):
    """Confirm that logout returns the user to the homepage."""
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_health_endpoint(client):
    """Confirm that the application health endpoint responds correctly."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}