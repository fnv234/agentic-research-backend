import os, base64, requests
from dotenv import load_dotenv

load_dotenv()
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Get OAuth token
creds = base64.b64encode(f"{PUBLIC_KEY}:{PRIVATE_KEY}".encode()).decode()
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {creds}"
}
data = {"grant_type": "client_credentials"}
r = requests.post("https://api.forio.com/v2/oauth/token", headers=headers, data=data)
r.raise_for_status()
token = r.json()["access_token"]
print("✅ Token acquired\n")

# List models in project
headers = {"Authorization": f"Bearer {token}"}
url = "https://api.forio.com/v2/model/mitcams/cyberriskmanagement-ransomeware-2023"
resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response:\n{resp.text}")
