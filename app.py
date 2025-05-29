import streamlit as st
import requests
import base64

st.title("Test GitHub Commit")

if st.button("Try Commit Test File"):
    GH_TOKEN = st.secrets["GH_TOKEN"]
    REPO = "growlitics/growlitics"
    BRANCH = "main"
    PATH = "saved_strategies/test_commit.txt"
    CONTENT = b"Hello from Streamlit Cloud!"
    COMMIT_MSG = "Test commit from Streamlit Cloud"

    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    # Check if file exists to get SHA
    get_url = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
    resp = requests.get(get_url, headers=headers, params={"ref": BRANCH})
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    put_data = {
        "message": COMMIT_MSG,
        "branch": BRANCH,
        "content": base64.b64encode(CONTENT).decode("utf-8"),
    }
    if sha:
        put_data["sha"] = sha

    put_resp = requests.put(get_url, headers=headers, json=put_data)

    st.write(f"PUT Status: {put_resp.status_code}")
    st.json(put_resp.json())
