"""Tests for the application entrypoint and auth blueprint."""

from werkzeug.security import generate_password_hash

from fakes import FakeConnection


def test_index_redirects_to_login_when_not_authenticated(app_client, fake_db):
    response = app_client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_index_renders_when_authenticated(app_client, fake_db):
    with app_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_email"] = "admin@example.com"
        sess["user_nome"] = "Admin"
    response = app_client.get("/")
    assert response.status_code == 200
    assert b"Curadoria" in response.data or b"biblioteca" in response.data


def test_login_get_renders_form(app_client, fake_db):
    response = app_client.get("/login")
    assert response.status_code == 200
    assert b"login" in response.data.lower() or b"email" in response.data.lower()


def test_login_empty_fields_redirects(app_client, fake_db):
    response = app_client.post("/login", data={"email": "", "senha": ""})
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_success_sets_session(app_client, fake_db):
    senha_hash = generate_password_hash("segredo123")
    fake_db(scripted=[
        {"id": 7, "email": "ana@example.com", "senha": senha_hash, "nome": "Ana"},
    ])
    response = app_client.post(
        "/login",
        data={"email": "ana@example.com", "senha": "segredo123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with app_client.session_transaction() as sess:
        assert sess["user_id"] == 7
        assert sess["user_nome"] == "Ana"


def test_login_wrong_password_stays_on_login(app_client, fake_db):
    senha_hash = generate_password_hash("correta")
    fake_db(scripted=[
        {"id": 1, "email": "a@b.com", "senha": senha_hash, "nome": "A"},
    ])
    response = app_client.post(
        "/login",
        data={"email": "a@b.com", "senha": "errada"},
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    with app_client.session_transaction() as sess:
        assert "user_id" not in sess


def test_login_unknown_user_redirects(app_client, fake_db):
    fake_db(scripted=[None])
    response = app_client.post(
        "/login",
        data={"email": "naoexiste@example.com", "senha": "x"},
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_logout_clears_session(app_client, fake_db):
    with app_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_email"] = "a@b.com"
    response = app_client.get("/logout")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    with app_client.session_transaction() as sess:
        assert "user_id" not in sess


def test_login_required_decorator_redirects_to_login(app_client, fake_db):
    fake_db(scripted=[{"total": 0}, []])
    response = app_client.get("/usuarios")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
