from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
AUTH = (ROOT / "app" / "api" / "auth.py").read_text(encoding="utf-8")
SECURITY = (ROOT / "app" / "security.py").read_text(encoding="utf-8")
ENV_PROD = (ROOT / ".env.production.example").read_text(encoding="utf-8")
GITIGNORE = (ROOT / ".gitignore").read_text(encoding="utf-8")
SCANNER = (ROOT / "templates" / "scanner.html").read_text(encoding="utf-8")
PUBLIC = (ROOT / "templates" / "public_pass.html").read_text(encoding="utf-8")


def test_production_requires_https_and_strong_secret():
    assert 'ENVIRONMENT == "production"' in MAIN
    assert 'PUBLIC_BASE_URL must use HTTPS in production.' in MAIN
    assert 'len(key) < 32' in SECURITY


def test_production_disables_demo_users_by_default():
    assert 'SEED_DEMO_USERS' in MAIN
    assert 'DEMO_ADMIN_PASSWORD' in MAIN
    assert 'DEMO_USER_PASSWORD' in MAIN
    assert '"true" if ENVIRONMENT != "production" else "false"' in MAIN
    assert 'SEED_DEMO_USERS=false' in ENV_PROD
    assert 'admin123' not in MAIN
    assert 'user123' not in MAIN


def test_sensitive_environment_files_are_ignored_but_safe_examples_are_kept():
    assert ".env" in GITIGNORE
    assert "!.env.example" in GITIGNORE
    assert "!.env.production.example" in GITIGNORE


def test_security_headers_and_generic_error_pages_exist():
    for header in [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Content-Security-Policy",
        "Strict-Transport-Security",
    ]:
        assert header in MAIN
    assert "Request unavailable." in MAIN
    assert "Page not found" not in MAIN
    assert "Never expose exception text" in MAIN


def test_public_pass_has_no_authenticated_layout_or_indexing():
    assert "{% extends" not in PUBLIC
    assert 'noindex,nofollow,noarchive' in PUBLIC
    assert "No account, wallet or personal profile data is displayed." in PUBLIC


def test_scanner_inline_javascript_removed_for_csp():
    assert '<script src="/static/js/scanner.js"></script>' in SCANNER
    assert "(() => {" not in SCANNER


def test_auth_cookie_is_http_only_same_site_and_short_lived():
    assert "httponly=True" in AUTH
    assert 'samesite="lax"' in AUTH
    assert "max_age=12 * 60 * 60" in AUTH


def test_docs_can_be_disabled():
    assert 'docs_url = "/docs" if ENABLE_DOCS else None' in MAIN
    assert 'openapi_url = "/openapi.json" if ENABLE_DOCS else None' in MAIN
