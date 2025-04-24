'''test files'''
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
    '''Test POST file method'''
    with open(TEST_FILE_PATH, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/files", files=files, timeout=TIMEOUT)
    assert response.status_code == 201
    assert "uploaded successfully" in response.json()["message"]


def test_list_files():
    '''Test GET files in storage'''
    response = requests.get(f"{BASE_URL}/files", timeout=TIMEOUT)
    assert response.status_code == 200
    assert "test.txt" in response.json()["files"]


def test_download_file():
    '''Test GET a file'''
    response = requests.get(f"{BASE_URL}/files/test.txt", timeout=TIMEOUT)
    assert response.status_code == 200
    assert response.content == TEST_FILE_CONTENT.encode()


def test_delete_file():
    '''Test DELETE a file'''
    response = requests.delete(f"{BASE_URL}/files/test.txt", timeout=TIMEOUT)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
