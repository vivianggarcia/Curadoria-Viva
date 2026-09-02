"""Shared pytest fixtures for the Curadoria-Viva test suite."""

import sys
from pathlib import Path

import pytest

# Make the project root importable so `from app import app`, `from db import
# conectar`, `from config import config`, etc. resolve from the test run.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def app_client():
    """Return a Flask test client for the real application.

    A real database is never touched: every route that opens a connection uses
    ``db.conectar``, which is patched by the ``fake_db`` fixture.
    """
    from app import app

    app.config.update(TESTING=True)
    app.config["SECRET_KEY"] = "test-secret-key"

    with app.test_client() as client:
        yield client


@pytest.fixture
def fake_db(monkeypatch):
    """Monkeypatch ``conectar`` in every module that imports it.

    Returns a factory: ``fake_db(scripted=[...])`` -> a ``FakeConnection`` whose
    scripts are used by the next request. Setting up a new connection for each
    request keeps the scripted results deterministic.
    """
    from fakes import FakeConnection

    installed = {}

    def setup(scripted=None, lastrowid=1):
        conn = FakeConnection(scripted=scripted)
        conn.lastrowid = lastrowid

        module_names = [
            "db",
            "routes.auth",
            "routes.usuarios",
            "routes.autores",
            "routes.livros",
            "routes.emprestimos",
            "routes.emprestimo_livro",
        ]
        for name in module_names:
            module = sys.modules.get(name)
            if module is None:
                continue
            if name == "db":
                monkeypatch.setattr(module, "conectar", lambda: conn)
            elif hasattr(module, "conectar"):
                monkeypatch.setattr(module, "conectar", lambda: conn)

        installed["conn"] = conn
        return conn

    yield setup
