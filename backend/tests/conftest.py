import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    # Context manager ensures lifespan runs (knowledge_base + init_db migrations).
    with TestClient(app) as c:
        yield c
