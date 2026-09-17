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


def test_health_endpoint(client):
    """Confirm that the application health endpoint responds correctly."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}