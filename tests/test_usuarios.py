"""Tests for the users (usuarios) blueprint."""

from werkzeug.security import check_password_hash


def _authed(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_email"] = "admin@example.com"
        sess["user_nome"] = "Admin"


def test_listar_renders_users(app_client, fake_db):
    _authed(app_client)
    users = [
        {"id": 1, "nome": "Ana", "email": "ana@x.com", "telefone": "11", "foto": "f.png"},
        {"id": 2, "nome": "Bia", "email": "bia@x.com", "telefone": "22", "foto": "g.png"},
    ]
    fake_db(scripted=[{"total": 2}, users])
    response = app_client.get("/usuarios")
    assert response.status_code == 200
    assert b"Ana" in response.data


def test_listar_anonymous_redirects_to_login(app_client, fake_db):
    fake_db(scripted=[{"total": 0}, []])
    response = app_client.get("/usuarios")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_add_requires_password(app_client, fake_db):
    _authed(app_client)
    response = app_client.post(
        "/usuarios/add",
        data={"nome": "Sem Senha", "email": "x@x.com", "telefone": "1", "senha": ""},
    )
    assert response.status_code == 200
    assert b"Senha" in response.data


def test_add_creates_user_and_hashes_password(app_client, fake_db):
    _authed(app_client)
    conn = fake_db()
    response = app_client.post(
        "/usuarios/add",
        data={"nome": "Novo", "email": "novo@x.com", "telefone": "999", "senha": "abc123"},
    )
    assert response.status_code == 302
    assert "/usuarios" in response.headers["Location"]
    assert conn.committed
    # The stored password must be a hash, never the plain value.
    insert_sql = conn.cursors[0].executed[0][0]
    assert "INSERT INTO usuarios" in insert_sql
    stored_hash = conn.cursors[0].executed[0][1][4]
    assert stored_hash != "abc123"
    assert check_password_hash(stored_hash, "abc123")


def test_delete_user_with_loans_is_blocked(app_client, fake_db):
    _authed(app_client)
    conn = fake_db(scripted=[(2,)])
    response = app_client.get("/usuarios/delete/3")
    assert response.status_code == 302
    assert "/usuarios" in response.headers["Location"]
    # No DELETE statement should have been executed.
    sqls = [sql for c in conn.cursors for sql, _ in c.executed]
    assert not any(sql.startswith("DELETE") for sql in sqls)


def test_delete_user_without_loans_removes(app_client, fake_db):
    _authed(app_client)
    conn = fake_db(scripted=[(0,)])
    response = app_client.get("/usuarios/delete/3")
    assert response.status_code == 302
    assert "/usuarios" in response.headers["Location"]
    assert conn.committed
    sqls = [sql for c in conn.cursors for sql, _ in c.executed]
    assert any(sql.startswith("DELETE FROM usuarios") for sql in sqls)


def test_edit_user_updates_fields(app_client, fake_db):
    _authed(app_client)
    conn = fake_db(scripted=[{"id": 1, "nome": "Antigo", "email": "a@x.com"}])
    response = app_client.post(
        "/usuarios/edit/1",
        data={"nome": "Novo Nome", "email": "novo@x.com", "telefone": "12", "foto": "", "senha": ""},
    )
    assert response.status_code == 302
    assert "/usuarios" in response.headers["Location"]
    assert conn.committed
    update_sql = conn.cursors[0].executed[0][0]
    assert update_sql.startswith("UPDATE usuarios")


def test_edit_user_update_with_senha_hashes(app_client, fake_db):
    _authed(app_client)
    conn = fake_db(scripted=[{"id": 1, "nome": "X", "email": "x@x.com"}])
    app_client.post(
        "/usuarios/edit/1",
        data={"nome": "X", "email": "x@x.com", "telefone": "1", "foto": "", "senha": "n104va"},
    )
    params = conn.cursors[0].executed[0][1]
    stored = params[-2] if "senha=%s" in conn.cursors[0].executed[0][0] else None
    assert stored is not None and stored != "n104va"
