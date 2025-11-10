import streamlit as st
import requests
import os
import sys
print(sys.executable)

BASE_URL = "http://localhost:8000"

st.title("Cloud Storage SDET Test Suite")

def print_log(msg):
    st.info(msg)

def upload_file(file):
    print_log("STEP: Uploading file...")
    files = {'file': (file.name, file)}
    r = requests.post(f"{BASE_URL}/files", files=files)
    st.write(f"Upload Status Code: {r.status_code}")
    st.json(r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text)
    assert r.status_code == 200
    file_id = r.json()["fileId"]
    print_log(f"Uploaded successfully! Assigned file_id: {file_id}")
    return file_id

def download_file(file_id):
    print_log(f"STEP: Downloading file (id={file_id})...")
    r = requests.get(f"{BASE_URL}/files/{file_id}")
    st.write(f"Download Status Code: {r.status_code}")
    if r.status_code == 200:
        st.download_button("Download file", data=r.content, file_name=f"downloaded_{file_id}.bin")
    else:
        st.error("Download failed.")
    return r.status_code == 200

def get_metadata(file_id):
    print_log(f"STEP: Fetching metadata for file id={file_id} ...")
    r = requests.get(f"{BASE_URL}/files/{file_id}/metadata")
    st.write(f"Metadata Status Code: {r.status_code}")
    st.json(r.json() if r.status_code == 200 else {"error": r.text})

def delete_file(file_id):
    print_log(f"STEP: Deleting file (id={file_id})...")
    r = requests.delete(f"{BASE_URL}/files/{file_id}")
    st.write(f"Delete Status Code: {r.status_code}")
    if r.status_code == 204:
        print_log("Delete successful!")
    else:
        st.error("Delete failed.")

def trigger_tiering():
    print_log("STEP: Triggering manual tiering process...")
    r = requests.post(f"{BASE_URL}/admin/tiering/run")
    st.write(f"Tiering Status Code: {r.status_code}")
    st.json(r.json() if r.status_code == 200 else {"error": r.text})

def get_stats():
    print_log("STEP: Fetching system stats...")
    r = requests.get(f"{BASE_URL}/admin/stats")
    st.write(f"Stats Status Code: {r.status_code}")
    st.json(r.json() if r.status_code == 200 else {"error": r.text})

# Streamlit interface
uploaded_file = st.file_uploader("Upload your 2MB file", type=["txt", "bin"])
file_id = st.text_input("Enter file ID for operations", "")

if uploaded_file and st.button("Upload File"):
    st.session_state.file_id = upload_file(uploaded_file)

if st.session_state.get("file_id"):
    fid = st.session_state.get("file_id")

    if st.button("Download File"):
        download_file(fid)

    if st.button("Get Metadata"):
        get_metadata(fid)

    if st.button("Delete File"):
        delete_file(fid)

if st.button("Trigger Tiering"):
    trigger_tiering()

if st.button("Get System Stats"):
    get_stats()
