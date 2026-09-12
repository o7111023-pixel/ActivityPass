"""HTTP integration tests.

These run in the normal project environment after `pip install -r requirements.txt`.
"""
import os
import importlib
from datetime import date, timedelta

import pytest

pytest.importorskip("jose")
pytest.importorskip("barcode")

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ACTIVITYPASS_SECRET_KEY", "test-secret-key-1234567890-abcdef")
os.environ.setdefault("ENABLE_DOCS", "false")
os.environ.setdefault("ALLOWED_HOSTS", "testserver,localhost")
os.environ.setdefault("PUBLIC_BASE_URL", "http://testserver")
os.environ.setdefault("SEED_DEMO_USERS", "true")
os.environ.setdefault("DEMO_ADMIN_PASSWORD", "test-admin-password")
os.environ.setdefault("DEMO_USER_PASSWORD", "test-user-password")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_activitypass.sqlite3")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
client_no_raise = TestClient(app, raise_server_exceptions=False)


def login(email="user@activitypass.demo", password=None):
    password = password or os.environ["DEMO_USER_PASSWORD"]
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=False)


def test_public_auth_pages_are_available_without_private_navigation():
    r = client.get("/login")
    assert r.status_code == 200
    assert "ActivityPass" in r.text
    assert "/dashboard" not in r.text


def test_private_page_redirects_to_login_without_session():
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_unknown_page_does_not_disclose_route_name_or_details():
    r = client.get("/this-page-does-not-exist")
    assert r.status_code == 404
    assert "Page not found" not in r.text
    assert "this-page-does-not-exist" not in r.text
    assert "Traceback" not in r.text
    assert "Request unavailable." in r.text


def test_unknown_and_invalid_requests_use_generic_error_text():
    unknown = client.get("/this-route-is-not-public")
    invalid = client.post("/login", data={"email": "not-an-email"}, follow_redirects=False)
    assert unknown.status_code == 404
    assert invalid.status_code == 422
    assert unknown.text == invalid.text
    assert "this-route-is-not-public" not in unknown.text
    assert "Invalid request" not in invalid.text
    assert "ActivityPass" not in invalid.text


def test_security_headers_are_present():
    r = client.get("/login")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]


def test_docs_are_disabled_when_configured():
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_demo_login_sets_secure_session_properties():
    r = login()
    assert r.status_code == 303
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "max-age=43200" in cookie


def test_authenticated_responses_are_not_cached():
    r = login()
    assert r.status_code == 303
    client.cookies.update(r.cookies)
    page = client.get("/wallet")
    assert page.status_code == 200
    assert page.headers["cache-control"] == "no-store, max-age=0"


def test_cross_origin_post_is_rejected():
    r = client.post(
        "/login",
        data={"email": "user@activitypass.demo", "password": os.environ["DEMO_USER_PASSWORD"]},
        headers={"Origin": "https://evil.example"},
        follow_redirects=False,
    )
    assert r.status_code == 403
    assert "evil.example" not in r.text
    assert r.text == "<!doctype html><html><body><p>Request unavailable.</p></body></html>"


def test_public_pass_does_not_require_login_and_has_no_account_data():
    from app.database import SessionLocal
    from app.models.pass_model import MembershipPass
    db = SessionLocal()
    p = db.query(MembershipPass).first()
    if p is None:
        pytest.skip("No demo pass exists yet")
    code = p.code
    db.close()
    r = client.get(f"/pass/view/{code}")
    assert r.status_code == 200
    assert "ActivityPass" in r.text
    assert "wallet" not in r.text.lower()
    assert "password_hash" not in r.text.lower()
    assert "noindex" in r.text.lower()


def test_sensitive_project_files_are_not_served():
    for path in ("/app/main.py", "/.env", "/test_activitypass.sqlite3", "/requirements.txt"):
        r = client.get(path)
        assert r.status_code == 404
        assert "Request unavailable." in r.text
        assert "Traceback" not in r.text
        assert "ActivityPass" not in r.text


def test_server_errors_are_generic_without_internal_details():
    @app.get("/__test_internal_error")
    def _raise_internal_error():
        raise RuntimeError("SECRET_INTERNAL_TEST_PATH")

    r = client_no_raise.get("/__test_internal_error")
    assert r.status_code == 500
    assert r.text == "<!doctype html><html><body><p>Request unavailable.</p></body></html>"
    assert "SECRET_INTERNAL_TEST_PATH" not in r.text
    assert "RuntimeError" not in r.text
    assert "Traceback" not in r.text


def test_non_admin_cannot_open_admin_area():
    r = login()
    assert r.status_code == 303
    client.cookies.update(r.cookies)
    page = client.get("/admin")
    assert page.status_code == 403
    assert page.text == "<!doctype html><html><body><p>Request unavailable.</p></body></html>"
