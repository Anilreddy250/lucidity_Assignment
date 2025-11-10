import requests
import time

BASE_URL = "http://your-api-endpoint"
test_file_path = "test_node_report.csv"
headers = {"Authorization": "Bearer your_admin_token"}

def test_upload_file():
    files = {'file': open(test_file_path, 'rb')}
    response = requests.post(f"{BASE_URL}/files", files=files)
    assert response.status_code == 200
    file_id = response.json()['id']
    return file_id

def test_download_file(file_id):
    response = requests.get(f"{BASE_URL}/files/{file_id}")
    assert response.status_code == 200

def test_get_metadata(file_id):
    response = requests.get(f"{BASE_URL}/files/{file_id}/metadata")
    assert response.status_code == 200

def test_delete_file(file_id):
    response = requests.delete(f"{BASE_URL}/files/{file_id}")
    assert response.status_code == 204

def test_run_manual_tiering():
    response = requests.post(f"{BASE_URL}/admin/tiering/run", headers=headers)
    assert response.status_code == 200

def test_get_stats():
    response = requests.get(f"{BASE_URL}/admin/stats", headers=headers)
    assert response.status_code == 200

# Edge test: 0-byte file
def test_zero_byte_upload():
    with open("empty_test.csv", "wb") as f: pass
    files = {'file': open("empty_test.csv", "rb")}
    response = requests.post(f"{BASE_URL}/files", files=files)
    assert response.status_code in [400, 422]  # Should fail

# Edge test: file just under 1MB
def test_under_1mb_upload():
    with open("small_test.csv", "wb") as f: f.write(b"0" * (1024*1024 - 1))
    files = {'file': open("small_test.csv", "rb")}
    response = requests.post(f"{BASE_URL}/files", files=files)
    assert response.status_code == 200

# Mock tier transitions (by manipulating timestamps in metadata)
# You may need to patch/mock the tiering date logic

