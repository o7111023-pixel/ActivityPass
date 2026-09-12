"""Shared pytest setup for isolated ActivityPass integration tests."""

import os
from pathlib import Path

# Keep integration tests deterministic: never reuse a developer's previous test DB.
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ACTIVITYPASS_SECRET_KEY", "test-secret-key-1234567890-abcdef")
os.environ.setdefault("ENABLE_DOCS", "false")
os.environ.setdefault("ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
os.environ.setdefault("PUBLIC_BASE_URL", "http://testserver")
os.environ.setdefault("SEED_DEMO_USERS", "true")
os.environ.setdefault("DEMO_ADMIN_PASSWORD", "test-admin-password")
os.environ.setdefault("DEMO_USER_PASSWORD", "test-user-password")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_activitypass.sqlite3")

test_db = Path("test_activitypass.sqlite3")
if test_db.exists():
    test_db.unlink()

# Unit tests build their own in-memory SQLite databases.
