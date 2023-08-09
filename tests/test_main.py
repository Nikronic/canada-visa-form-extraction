# core
from starlette.testclient import TestClient
from fastapi import status
import json
# Ours: API
from cvfe.main import app
# helpers
from pathlib import Path


# globals
test_client = TestClient(app=app)
ASSETS_PATH = Path('tests/assets')
DUMMY_FILES_PATH = ASSETS_PATH / Path('dummy')
def test_read_main():
    response = test_client.get('/')
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_bad_files():
    files = {
        'form_5257': open(DUMMY_FILES_PATH / Path('dummy_1.pdf'), 'rb'),
        'form_5645': open(DUMMY_FILES_PATH / Path('dummy_2.pdf'), 'rb')
    }

    response = test_client.post(
        url='/cvfe/v1/convert/adobe_xfa/',
        files=files
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

