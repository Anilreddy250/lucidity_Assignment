import pytest
import requests
import os

BASE_URL = "http://localhost:8000"
TEST_FILE = "twomb.txt"  # Ensure this file is present and is about 2MB in size

def log(msg):
    print(f"[LOG] {msg}")

def upload_file(file_path):
    log(f"Uploading file: {file_path}")
    with open(file_path, "rb") as f:
        files = {'file': (os.path.basename(file_path), f)}
        r = requests.post(f"{BASE_URL}/files", files=files)
    log(f"Upload status code: {r.status_code}, response: {r.text}")
    assert r.status_code == 200
    file_id = r.json()["fileId"]
    log(f"Uploaded file_id: {file_id}")
    return file_id

def test_file_upload_download_delete():
    file_id = upload_file(TEST_FILE)
    
    # Download
    log(f"Downloading file with id: {file_id}")
    r = requests.get(f"{BASE_URL}/files/{file_id}")
    log(f"Download status code: {r.status_code}")
    assert r.status_code == 200

    # Delete
    log(f"Deleting file with id: {file_id}")
    r = requests.delete(f"{BASE_URL}/files/{file_id}")
    log(f"Delete status code: {r.status_code}")
    assert r.status_code == 204

def test_metadata_after_upload():
    file_id = upload_file(TEST_FILE)
    log(f"Fetching metadata for file id: {file_id}")
    r = requests.get(f"{BASE_URL}/files/{file_id}/metadata")
    log(f"Metadata response: {r.status_code}, {r.text}")
    assert r.status_code == 200
    meta = r.json()
    assert meta["tier"] == "HOT"
    assert meta["size"] >= 2*1024*1024  # 2MB

def test_error_invalid_file_id():
    log("Testing GET with invalid file ID")
    r = requests.get(f"{BASE_URL}/files/not_a_valid_id")
    log(f"Invalid file ID status: {r.status_code}")
    assert r.status_code in [400, 404]

def test_get_stats():
    log("Fetching system stats")
    r = requests.get(f"{BASE_URL}/admin/stats")
    log(f"Stats response: {r.status_code}, {r.text}")
    assert r.status_code == 200
    stats = r.json()
    assert "totalFiles" in stats
    assert "hotTier" in stats

def test_tiering_process():
    file_id = upload_file(TEST_FILE)
    log("Triggering manual tiering process")
    r = requests.post(f"{BASE_URL}/admin/tiering/run")
    log(f"Tiering trigger response: {r.status_code}, {r.text}")
    r = requests.get(f"{BASE_URL}/files/{file_id}/metadata")
    meta = r.json()
    log(f"Post-tiering metadata: {meta}")
    assert meta["tier"] in ["HOT", "WARM", "COLD"]

def test_concurrent_access():
    import threading
    results = []

    def upload_and_delete():
        try:
            file_id = upload_file(TEST_FILE)
            log(f"[Thread] Deleting file: {file_id}")
            requests.delete(f"{BASE_URL}/files/{file_id}")
            results.append(True)
        except Exception as e:
            log(f"[Thread] Error: {e}")
            results.append(False)

    threads = [threading.Thread(target=upload_and_delete) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    log("Concurrent access test results: " + str(results))
    assert all(results)

if __name__ == "__main__":
    pytest.main()
