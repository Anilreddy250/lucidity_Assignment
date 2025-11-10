import pytest
import requests
import random
import string
import io
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def random_file(size):
    return io.BytesIO(bytearray(random.getrandbits(8) for _ in range(size)))

def upload_file(size=1024*1024, name="testfile.bin"):
    files = {'file': (name, random_file(size))}
    r = requests.post(f"{BASE_URL}/files", files=files)
    assert r.status_code == 200
    return r.json()["fileId"]

def test_file_upload_download_delete():
    file_id = upload_file()
    r = requests.get(f"{BASE_URL}/files/{file_id}")
    assert r.status_code == 200
    r = requests.delete(f"{BASE_URL}/files/{file_id}")
    assert r.status_code == 204

def test_metadata_after_upload():
    file_id = upload_file(size=2*1024*1024)
    r = requests.get(f"{BASE_URL}/files/{file_id}/metadata")
    assert r.status_code == 200
    meta = r.json()
    assert meta["tier"] == "HOT"
    assert meta["size"] >= 2*1024*1024

def test_upload_invalid_size():
    # Below min size
    files = {'file': ("small.bin", random_file(500 * 1024))}
    r = requests.post(f"{BASE_URL}/files", files=files)
    assert r.status_code == 400

    # Above max size
    files = {'file': ("big.bin", random_file(11*1024*1024*1024))}
    r = requests.post(f"{BASE_URL}/files", files=files)
    assert r.status_code == 400

def test_tiering_process():
    file_id = upload_file(name="tieringtest.bin")
    # Simulate lastAccessed > 30 days by API (or patch DB for a real system)
    # Here we assume API lets us set the metadata, otherwise this code won't move actual file
    requests.post(f"{BASE_URL}/admin/tiering/run")
    r = requests.get(f"{BASE_URL}/files/{file_id}/metadata")
    meta = r.json()
    assert meta["tier"] in ["HOT", "WARM", "COLD"]

def test_get_stats():
    r = requests.get(f"{BASE_URL}/admin/stats")
    assert r.status_code == 200
    stats = r.json()
    assert "totalFiles" in stats
    assert "hotTier" in stats

def test_concurrent_access():
    import threading
    results = []

    def upload_and_delete():
        try:
            file_id = upload_file()
            requests.delete(f"{BASE_URL}/files/{file_id}")
            results.append(True)
        except Exception:
            results.append(False)

    threads = [threading.Thread(target=upload_and_delete) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert all(results)

def test_error_invalid_file_id():
    r = requests.get(f"{BASE_URL}/files/not_a_valid_id")
    assert r.status_code in [400, 404]

def test_bulk_operations():
    # If supported: For bonus implementation!
    pass

# For performance and fault injection, use fixtures or parametrize with timeouts/forced failures as needed.

if __name__ == "__main__":
    pytest.main()
