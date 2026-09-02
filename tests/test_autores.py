"""Tests for the authors (autores) blueprint."""


def _authed(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_email"] = "admin@example.com"
        sess["user_nome"] = "Admin"


def test_listar_autores_renders(app_client, fake_db):
    _authed(app_client)
    autores = [
        {"id": 1, "nome": "Machado de Assis"},
        {"id": 2, "nome": "Clarice Lispector"},
    ]
    fake_db(scripted=[{"total": 2}, autores])
    response = app_client.get("/autores")
    assert response.status_code == 200
    assert b"Machado de Assis" in response.data


def test_listar_autores_search_uses_like(app_client, fake_db):
    _authed(app_client)
    conn = fake_db(scripted=[{"total": 0}, []])
    response = app_client.get("/autores?q=machado")
    assert response.status_code == 200
    # The generated COUNT query must include the LIKE filter.
    count_sql = conn.cursors[0].executed[0][0]
    assert "LIKE" in count_sql


def test_add_autor_inserts(app_client, fake_db):
    conn = fake_db()
    response = app_client.post("/autores/add", data={"nome": "Novo Autor"})
    assert response.status_code == 302
    assert "/autores" in response.headers["Location"]
    assert conn.committed
    sql = conn.cursors[0].executed[0][0]
    assert "INSERT INTO autores" in sql


def test_edit_autor_updates(app_client, fake_db):
    conn = fake_db(scripted=[{"id": 1, "nome": "Antigo"}])
    response = app_client.post("/autores/edit/1", data={"nome": "Editado"})
    assert response.status_code == 302
    assert "/autores" in response.headers["Location"]
    assert conn.committed
    assert any(sql.startswith("UPDATE autores") for sql, _ in conn.cursors[0].executed)


def test_delete_autor_with_books_blocked(app_client, fake_db):
    conn = fake_db(scripted=[(3,)])
    response = app_client.get("/autores/delete/1")
    assert response.status_code == 302
    assert "/autores" in response.headers["Location"]
    sqls = [sql for c in conn.cursors for sql, _ in c.executed]
    assert not any(sql.startswith("DELETE") for sql in sqls)


def test_delete_autor_without_books_removes(app_client, fake_db):
    conn = fake_db(scripted=[(0,)])
    response = app_client.get("/autores/delete/1")
    assert response.status_code == 302
    assert conn.committed
    sqls = [sql for c in conn.cursors for sql, _ in c.executed]
    assert any(sql.startswith("DELETE FROM autores") for sql in sqls)
