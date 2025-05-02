'''test distributed files'''
import os
import pytest
import requests

TEST_FILE_PATH = "tests/test.txt"
TEST_FILE_CONTENT =  "This is a test file\n"
BASE_URL = "http://127.0.0.1:5000"
TIMEOUT = 10


@pytest.fixture(scope="module", autouse=True)
def prepare_test_file():
    '''Create and remove test file automatically'''
    os.makedirs("tests", exist_ok=True)
    with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(TEST_FILE_CONTENT)
    yield
    os.remove(TEST_FILE_PATH)


def test_upload_file():
    '''Test distributed POST method'''
    with open(TEST_FILE_PATH, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/files", files=files,timeout=TIMEOUT)
    assert response.status_code == 201
    assert "upload successefully" in response.json()["message"]
    response = requests.get("http://127.0.0.1:5004/chord/info", timeout=TIMEOUT)
    assert "test.txt" in response.json()["files"]


def test_get_file():
    '''Test GET file in all nodes'''
    for i in range(0, 4):
        response = requests.get(f"http://127.0.0.1:500{i}/files", timeout=TIMEOUT)
        assert len(response.json()["files"]) == 0

    response = requests.get("http://127.0.0.1/files/test.txt", timeout=TIMEOUT)
    assert "test.txt" in response.json()
