import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure the app folder is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Application-Source-Code")))
from backend import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ==========================================
# /register Tests
# ==========================================

@patch("backend.get_db_connection")
def test_register_success(mock_get_db, client):
    # Mock DB connection & cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    payload = {"username": "testuser", "password": "securepassword"}
    response = client.post("/register", json=payload)

    # Assertions
    assert response.status_code == 201
    assert response.get_json() == {"message": "User registered successfully"}
    
    # Verify DB interactions
    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        ("testuser", "securepassword")
    )
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


# ==========================================
# /login Tests
# ==========================================

@patch("backend.get_db_connection")
def test_login_success(mock_get_db, client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Simulate DB returning an existing user row
    mock_cursor.fetchone.return_value = (1, "testuser", "securepassword")

    payload = {"username": "testuser", "password": "securepassword"}
    response = client.post("/login", json=payload)

    assert response.status_code == 200
    assert response.get_json() == {"message": "Login successful"}
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        ("testuser", "securepassword")
    )


@patch("backend.get_db_connection")
def test_login_invalid_credentials(mock_get_db, client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Simulate DB returning None (user not found / wrong password)
    mock_cursor.fetchone.return_value = None

    payload = {"username": "wronguser", "password": "wrongpassword"}
    response = client.post("/login", json=payload)

    assert response.status_code == 401
    assert response.get_json() == {"message": "Invalid credentials"}