# core
from starlette.testclient import TestClient
from fastapi import status
import json
# Ours: API
from cvfe.main import app


# globals
test_client = TestClient(app=app)
def test_read_main():
    response = test_client.get('/')
    assert response.status_code == status.HTTP_404_NOT_FOUND

