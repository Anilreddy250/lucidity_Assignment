import pytest
import requests
import os

BASE_URL = "http://localhost:8000"
TEST_FILE = "twomb.txt"  # Ensure this file exists and is about 2MB

def log(msg):
    print(f"\n========================\n{msg}\n========================")

def upload_file(file_path):
    log(f"STEP: Start Uploading file: {file_path}")
    with open(file_path, "rb") as f:
        files = {'file': (os.path.basename(file_path), f)}
        r = requests.post(f"{BASE_URL}/files", files=files)
    print(f"Upload request sent, status code: {r.status_code}")
    print(f"Upload response content: {r.text}")
    assert r.status_code == 200
    file_id = r.json()["fileId"]
    print(f"Uploaded successfully! Assigned file_id: {file_id}")
    log(f"STEP: End Upload for {file_path}")
    return file_id

def test_file_upload_download_delete():
    log("TEST: File Upload-Download-Delete START")
    file_id = upload_file(TEST_FILE)
    
    log(f"STEP: Downloading file with id: {file_id}")
    r = requests.get(f"{BASE_URL}/files/{file_id}")
    print(f"Download request sent, status code: {r.status_code}")
    assert r.status_code == 200
    print("Download successful!")

    log(f"STEP: Deleting file with id: {file_id}")
    r = requests.delete(f"{BASE_URL}/files/{file_id}")
    print(f"Delete request sent, status code: {r.status_code}")
    assert r.status_code == 204
    print("Delete successful!")
    log("TEST: File Upload-Download-Delete END")

def test_metadata_after_upload():
    log("TEST: Metadata After Upload START")
    file_id = upload_file(TEST_FILE)
    log(f"STEP: Fetching metadata for file id: {file_id}")
    r = requests.get(f"{BASE_URL}/files/{file_id}/metadata")
    print(f"Metadata request sent, status code: {r.status_code}, response: {r.text}")
    assert r.status_code == 200
    meta = r.json()
    print(f"Metadata tier: {meta['tier']}, size: {meta['size']}")
    assert meta["tier"] == "HOT"
    assert meta["size"] >= 2*1024*1024  # 2MB
    print("Metadata checks passed!")
    log("TEST: Metadata After Upload END")

def test_error_invalid_file_id():
    log("TEST: Error Invalid File ID START")
    print("Sending GET request with invalid file ID...")
    r = requests.get(f"{BASE_URL}/files/not_a_valid_id")
    print(f"Status code for invalid file ID: {r.status_code}")
    assert r.status_code in [400, 404]
    print("Invalid file ID error check passed!")
    log("TEST: Error Invalid File ID END")

def test_get_stats():
    log("TEST: Get System Stats START")
    print("Sending GET request to fetch system stats...")
    r = requests.get(f"{BASE_URL}/admin/stats")
    print(f"Stats request sent, status code: {r.status_code}, content: {r.text}")
    assert r.status_code == 200
    stats = r.json()
    print(f"System stats keys: {list(stats.keys())}")
    assert "totalFiles" in stats
    assert "hotTier" in stats
    print("System stats checks passed!")
    log("TEST: Get System Stats END")

def test_tiering_process():
    log("TEST: Manual Tiering Process START")
    file_id = upload_file(TEST_FILE)
    print("Triggering manual tiering process...")
    r = requests.post(f"{BASE_URL}/admin/tiering/run")
    print(f"Tiering trigger request sent, status code: {r.status_code}, response: {r.text}")
    r = requests.get(f"{BASE_URL}/files/{file_id}/metadata")
    meta = r.json()
    print(f"Metadata after tiering: tier={meta['tier']}")
    assert meta["tier"] in ["HOT", "WARM", "COLD"]
    print("Tiering process check passed!")
    log("TEST: Manual Tiering Process END")

def test_concurrent_access():
    log("TEST: Concurrent Access START")
    import threading
    results = []

    def upload_and_delete():
        try:
            file_id = upload_file(TEST_FILE)
            print(f"[Thread] Deleting file: {file_id}")
            r = requests.delete(f"{BASE_URL}/files/{file_id}")
            print(f"[Thread] Delete status: {r.status_code}")
            results.append(r.status_code == 204)
        except Exception as e:
            print(f"[Thread] Error: {e}")
            results.append(False)

    threads = [threading.Thread(target=upload_and_delete) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("Concurrent access test results:", results)
    assert all(results)
    print("Concurrent access test passed!")
    log("TEST: Concurrent Access END")

if __name__ == "__main__":
    log("=== RUNNING ALL TEST CASES ===")
    pytest.main()
    log("=== TEST RUN COMPLETE ===")
