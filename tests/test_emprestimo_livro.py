"""Tests for the loan-book relation (emprestimo_livro) blueprint."""


def _authed(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_email"] = "admin@example.com"
        sess["user_nome"] = "Admin"


def test_listar_renders(app_client, fake_db):
    _authed(app_client)
    emprestimos = [{"id": 1, "data_emprestimo": "2026-01-01"}]
    livros = [{"id": 3, "titulo": "Livro A", "capa": None}]
    dados = [{"id": 1, "emprestimo": 1, "id_livro": 3, "livro": "Livro A", "capa": None}]
    fake_db(scripted=[emprestimos, livros, {"total": 1}, dados])
    response = app_client.get("/emprestimo_livro")
    assert response.status_code == 200
    assert b"Livro A" in response.data


def test_listar_anonymous_redirects(app_client, fake_db):
    fake_db(scripted=[[], [], {"total": 0}, []])
    response = app_client.get("/emprestimo_livro")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_add_relacao_duplicate_blocked(app_client, fake_db):
    conn = fake_db(
        scripted=[
            {"id": 1, "data_emprestimo": "x"},
            {"id": 3, "titulo": "Livro"},
            (1,),  # COUNT() -> relation already exists
        ]
    )
    response = app_client.post(
        "/emprestimo_livro/add",
        data={"id_emprestimo": "1", "id_livro": "3"},
    )
    assert response.status_code == 302
    assert "/emprestimo_livro/add" in response.headers["Location"]
    # Duplicate path: no INSERT should have been committed.
    assert not conn.committed


def test_add_relacao_success(app_client, fake_db):
    conn = fake_db(
        scripted=[
            {"id": 1, "data_emprestimo": "x"},
            {"id": 3, "titulo": "Livro"},
            (0,),  # COUNT() -> relation does not exist yet
        ]
    )
    response = app_client.post(
        "/emprestimo_livro/add",
        data={"id_emprestimo": "1", "id_livro": "3"},
    )
    assert response.status_code == 302
    sqls = [sql for c in conn.cursors for sql, _ in c.executed]
    assert any(sql.startswith("INSERT INTO emprestimo_livro") for sql in sqls)
    assert conn.committed


def test_delete_relacao_removes(app_client, fake_db):
    conn = fake_db()
    response = app_client.get("/emprestimo_livro/delete/1")
    assert response.status_code == 302
    assert conn.committed
    sqls = [sql for c in conn.cursors for sql, _ in c.executed]
    assert any(sql.startswith("DELETE FROM emprestimo_livro") for sql in sqls)
