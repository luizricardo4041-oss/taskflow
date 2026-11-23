import pytest
from src.app import app as flask_app, init_db
import src.app as app_module


@pytest.fixture()
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_taskflow.db"
    monkeypatch.setattr(app_module, "DATABASE", str(test_db))

    init_db()

    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        yield client


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"TaskFlow" in response.data


def test_create_task(client):
    response = client.post(
        "/tasks",
        data={
            "title": "Planejar entregas",
            "priority": "Alta"
        }
    )

    assert response.status_code == 302

    page = client.get("/")
    assert b"Planejar entregas" in page.data


def test_empty_title_is_rejected(client):
    client.post("/tasks", data={"title": "   "})

    page = client.get("/")
    assert b"Informe um t\xc3\xadtulo" in page.data


def test_update_task_status(client):
    client.post(
        "/tasks",
        data={"title": "Validar sistema"}
    )

    client.post(
        "/tasks/1/update",
        data={
            "title": "Validar sistema",
            "description": "",
            "priority": "Média",
            "status": "Concluída"
        }
    )

    page = client.get("/")
    assert b"Conclu\xc3\xadda" in page.data


def test_delete_task(client):
    client.post(
        "/tasks",
        data={"title": "Tarefa temporária"}
    )

    client.post("/tasks/1/delete")

    page = client.get("/")
    assert b"Tarefa tempor\xc3\xa1ria" not in page.data


def test_search_filter(client):
    client.post(
        "/tasks",
        data={"title": "Conferir estoque"}
    )

    page = client.get("/?q=estoque")
    assert b"Conferir estoque" in page.data

    page = client.get("/?q=cliente-inexistente")
    assert b"Nenhuma tarefa encontrada" in page.data
