import json
from pathlib import Path
from typing import Any

from cvfe.convert.adobe_xfa import process

# globals
ASSETS_PATH = Path("tests/assets")
DUMMY_FILES_PATH = ASSETS_PATH / Path("dummy")
FILLED_FILES_PATH = ASSETS_PATH / Path("filled")


def test_process():
    with open(
        "tests/assets/filled/response_fake_correct.json", "rb"
    ) as correct_response_path:
        correct_response: dict[str, dict[str, Any]] = json.load(correct_response_path)

    given_response: dict[str, dict[str, Any]] = process(src_dir=FILLED_FILES_PATH)

    assert given_response == correct_response
