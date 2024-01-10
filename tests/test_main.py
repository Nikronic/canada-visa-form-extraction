import json
from pathlib import Path
from typing import Any

import pytest

# if API deps are not installed, ignore running tests
pytest.importorskip(
    modname="fastapi",
    reason=f"API dependencies are not installed. "
    f"Ignoring all API tests and marking it as 'no-error'",
)

from fastapi import status
from starlette.testclient import TestClient

from cvfe.main import app

# globals
test_client = TestClient(app=app)
ASSETS_PATH = Path("tests/assets")
DUMMY_FILES_PATH = ASSETS_PATH / Path("dummy")
FILLED_FILES_PATH = ASSETS_PATH / Path("filled")


# some notes:
#   1. no need to define headers for requests: for some reason it throws error in multipart


def test_read_main():
    response = test_client.get("/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_bad_files():
    files = {
        "form_5257": open(DUMMY_FILES_PATH / Path("dummy_1.pdf"), "rb"),
        "form_5645": open(DUMMY_FILES_PATH / Path("dummy_2.pdf"), "rb"),
    }

    response = test_client.post(url="/cvfe/v1/convert/adobe_xfa/", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_good_files():
    files = {
        "form_5257": open(FILLED_FILES_PATH / Path("imm5257e_fake.pdf"), "rb"),
        "form_5645": open(FILLED_FILES_PATH / Path("imm5645e_fake.pdf"), "rb"),
    }

    response = test_client.post(url="/cvfe/v1/convert/adobe_xfa/", files=files)

    assert response.status_code == status.HTTP_200_OK

    correct_response: dict[str, dict[str, Any]] = open(
        "tests/assets/filled/response_fake_correct.json", "rb"
    )
    assert response.json() == json.load(correct_response)
