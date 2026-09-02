"""Tests for the books (livros) blueprint."""


def _authed(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_email"] = "admin@example.com"
        sess["user_nome"] = "Admin"


def test_listar_livros_renders(app_client, fake_db):
    _authed(app_client)
    autores = [{"id": 1, "nome": "Autor A"}]
    livros = [{"id": 10, "titulo": "Dom Casmurro", "ano": 1899, "capa": None, "autor": "Autor A"}]
    conn = fake_db(scripted=[autores, {"total": 1}, livros])
    response = app_client.get("/livros")
    assert response.status_code == 200
    assert b"Dom Casmurro" in response.data
    # Livros listing joins livros with autores.
    select_sql = conn.cursors[0].executed[2][0]
    assert "JOIN autores" in select_sql or "join autores" in select_sql.lower()


def test_listar_livros_anonymous_redirects(app_client, fake_db):
    fake_db(scripted=[{}, {"total": 0}, []])
    response = app_client.get("/livros")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_add_livro_valid_ano_inserts(app_client, fake_db):
    _authed(app_client)
    conn = fake_db(scripted=[{"id": 1, "nome": "Autor A"}])
    response = app_client.post(
        "/livros/add",
        data={"titulo": "Livro Novo", "ano": "2001", "id_autor": "1", "capa": ""},
    )
    assert response.status_code == 302
    assert "/livros" in response.headers["Location"]
    assert conn.committed
    sqls = [sql for c in conn.cursors for sql, _ in c.executed]
    assert any(sql.startswith("INSERT INTO livros") for sql in sqls)


def test_add_livro_invalid_ano_rejected(app_client, fake_db):
    _authed(app_client)
    fake_db(scripted=[{"id": 1, "nome": "Autor A"}])
    response = app_client.post(
        "/livros/add",
        data={"titulo": "Livro", "ano": "1800", "id_autor": "1", "capa": ""},
    )
    # Returns an inline script that alerts about the invalid year.
    assert b"1900" in response.data
    assert b"alert" in response.data.lower()


def test_add_livro_non_numeric_ano_rejected(app_client, fake_db):
    _authed(app_client)
    fake_db(scripted=[{"id": 1, "nome": "Autor A"}])
    response = app_client.post(
        "/livros/add",
        data={"titulo": "Livro", "ano": "abc", "id_autor": "1", "capa": ""},
    )
    assert b"anos" in response.data.lower() or b"invalido" in response.data.lower()


def test_delete_livro_with_loan_blocked(app_client, fake_db):
    _authed(app_client)
    conn = fake_db(scripted=[(2,)])
    response = app_client.get("/livros/delete/5")
    assert response.status_code == 302
    assert "/livros" in response.headers["Location"]
    sqls = [sql for c in conn.cursors for sql, _ in c.executed]
    assert not any(sql.startswith("DELETE FROM livros") for sql in sqls)


def test_edit_livro_updates(app_client, fake_db):
    conn = fake_db(scripted=[{"id": 1, "titulo": "Antigo", "id_autor": 1, "ano": 1, "capa": ""}])
    response = app_client.post(
        "/livros/edit/1",
        data={"titulo": "Atualizado", "id_autor": "2", "ano": "2020", "capa": ""},
    )
    assert response.status_code == 302
    assert "/livros" in response.headers["Location"]
    assert conn.committed
    assert any(sql.startswith("UPDATE livros") for sql, _ in conn.cursors[0].executed)
