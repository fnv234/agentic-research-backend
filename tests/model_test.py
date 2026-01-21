import os, base64, requests
from dotenv import load_dotenv

load_dotenv()
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# get OAuth token
creds = base64.b64encode(f"{PUBLIC_KEY}:{PRIVATE_KEY}".encode()).decode()
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {creds}"
}
data = {"grant_type": "client_credentials"}
r = requests.post("https://api.forio.com/v2/oauth/token", headers=headers, data=data)
r.raise_for_status()
token = r.json()["access_token"]

# list all projects under your org
headers = {"Authorization": f"Bearer {token}"}
resp = requests.get("https://api.forio.com/v2/project", headers=headers)
print("Status:", resp.status_code)
print("Response:", resp.text)

resp = requests.get("https://api.forio.com/v2/model/acme-simulations/sample-python-model")
print(resp.text)

