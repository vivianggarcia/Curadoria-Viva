"""Tests for the loans (emprestimos) blueprint."""

import datetime


def _authed(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_email"] = "admin@example.com"
        sess["user_nome"] = "Admin"


def test_listar_emprestimos_renders(app_client, fake_db):
    _authed(app_client)
    loans = [
        {
            "id": 1,
            "usuario": "Ana",
            "foto_usuario": None,
            "data_emprestimo": datetime.date(2026, 1, 1),
            "data_devolucao": datetime.date(2026, 2, 1),
            "livro": "A Hora da Estrela",
            "id_livro": 3,
            "capa": None,
        }
    ]
    fake_db(scripted=[{"total": 1}, loans])
    response = app_client.get("/emprestimos")
    assert response.status_code == 200
    assert b"A Hora da Estrela" in response.data


def test_add_emprestimo_with_invalid_dates_rejected(app_client, fake_db):
    conn = fake_db(scripted=[{"id": 1, "nome": "Ana"}, {"id": 3, "titulo": "Livro"}])
    response = app_client.post(
        "/emprestimos/add",
        data={
            "id_usuario": "1",
            "data_emprestimo": "2026-05-10",
            "data_devolucao": "2026-05-01",
            "id_livro": ["3"],
        },
    )
    # Data de devolução before data de empréstimo -> inline alert script.
    assert b"alert" in response.data.lower()


def test_add_emprestimo_success_inserts(app_client, fake_db):
    conn = fake_db(
        scripted=[
            {"id": 1, "nome": "Ana"},
            {"id": 3, "titulo": "Livro"},
        ],
        lastrowid=42,
    )
    response = app_client.post(
        "/emprestimos/add",
        data={
            "id_usuario": "1",
            "data_emprestimo": "2026-05-10",
            "data_devolucao": "2026-06-10",
            "id_livro": ["3"],
        },
    )
    assert response.status_code == 302
    assert "/emprestimos" in response.headers["Location"]
    assert conn.committed
    # The insert into emprestimos happens first, then the join rows.
    sqls = [sql for sql, _ in conn.cursors[0].executed]
    assert any(sql.startswith("INSERT INTO emprestimos") for sql in sqls)
    assert any(sql.startswith("INSERT INTO emprestimo_livro") for sql in sqls)


def test_delete_emprestimo_existing_succeeds(app_client, fake_db):
    conn = fake_db(scripted=[(1,)])
    response = app_client.get("/emprestimos/delete/9")
    # On success the route returns an inline JS success message with 200.
    assert response.status_code == 200
    assert b"exclu" in response.data.lower() or b"sucesso" in response.data.lower()
    assert conn.committed
    sqls = [sql for sql, _ in conn.cursors[0].executed]
    assert any(sql.startswith("DELETE FROM emprestimo_livro") for sql in sqls)
    assert any(sql.startswith("DELETE FROM emprestimos") for sql in sqls)


def test_delete_emprestimo_not_found(app_client, fake_db):
    conn = fake_db(scripted=[(0,)])
    response = app_client.get("/emprestimos/delete/9")
    assert response.status_code == 200
    assert b"n" in response.data and (b"encontrado" in response.data.lower())
    assert not conn.committed


def test_edit_emprestimo_updates(app_client, fake_db):
    conn = fake_db(scripted=[{"id": 9, "id_livro": 3}])
    response = app_client.post(
        "/emprestimos/edit/9",
        data={
            "id_usuario": "1",
            "id_livro": "3",
            "data_emprestimo": "2026-01-01",
            "data_devolucao": "2026-02-01",
        },
    )
    assert response.status_code == 302
    assert "/emprestimos" in response.headers["Location"]
    assert conn.committed
    sqls = [sql for sql, _ in conn.cursors[0].executed]
    assert any(sql.startswith("UPDATE emprestimos") for sql in sqls)
